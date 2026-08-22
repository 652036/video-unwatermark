"""Public paste-link JSON fallbacks. No API keys, no encrypted tickets, no cookies."""

from __future__ import annotations

import hashlib
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import httpx

from ..urls import is_douyin, is_kuaishou
from ..util import hostname_of, platform_of

log = logging.getLogger("unwatermark")

# Discovered 2026-08-18 by fetching public pages / docs (no brute-force, no git clone):
# - 17change.cn: POST https://api4.17change.cn/parse/video  body {link} + md5 headers
#   Kuaishou works; Douyin currently returns code 5001 (page structure changed).
# - Evil0ctal demo: GET https://douyin.wtf/api/hybrid/video_data?url=...
#   api.douyin.wtf is 404; live host is douyin.wtf. Unauthenticated JSON.
# - api.yujn.cn: GET /api/dy_jx.php?msg=  simple JSON (may rate-limit).
# - tenapi.cn: POST /v2/video form url=  (host was Cloudflare 502 this run).
# Skip:
# - snapany.com official extract API requires a developer key
# - v2ob.com: NEXT_PUBLIC_PARSER_API_URL is unset in the homepage JS
# - hellotik.app: needs parseTicket + request encryption
# TikTok dual: do not guess a TikTok twin for a Douyin id. tikwm rejected Douyin URLs.

ORIGIN_17 = "https://17change.cn"
PARSE_17 = "https://api4.17change.cn/parse/video"
EVIL_HYBRID = "https://douyin.wtf/api/hybrid/video_data"
YUJN_DY = "https://api.yujn.cn/api/dy_jx.php"
TENAPI_V2 = "https://tenapi.cn/v2/video"

SITE_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

BACKEND_TIMEOUT = 12.0
RACE_TIMEOUT = 14.5


def _sign_17(body: dict) -> dict:
    keys = sorted(body)
    joined = "&".join(f"{k}={body[k]}" for k in keys)
    ts = str(int(time.time() * 1000))
    nonce = hex(random.getrandbits(40))[2:]
    raw = f"{joined}&Timestamp={ts}&nonce={nonce}&url={ORIGIN_17}"
    sig = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return {
        "User-Agent": SITE_UA,
        "Content-Type": "application/json",
        "Origin": ORIGIN_17,
        "Referer": "https://17change.cn/fastools/parsevideo",
        "timestamp": ts,
        "nonce": nonce,
        "signature": sig,
    }


def _first_http(value: Any) -> str | None:
    if isinstance(value, str) and value.startswith("http"):
        return value
    if isinstance(value, list):
        for item in value:
            got = _first_http(item)
            if got:
                return got
    if isinstance(value, dict):
        for key in ("url_list", "urlList", "url", "play", "src", "uri"):
            if key in value:
                got = _first_http(value[key])
                if got:
                    return got
    return None


def _walk_http(obj: Any, pred=None, _depth: int = 0) -> str | None:
    if _depth > 12:
        return None
    if pred and pred(obj):
        got = _first_http(obj)
        if got:
            return got
    if isinstance(obj, dict):
        for v in obj.values():
            found = _walk_http(v, pred, _depth + 1)
            if found:
                return found
    elif isinstance(obj, list):
        for v in obj[:30]:
            found = _walk_http(v, pred, _depth + 1)
            if found:
                return found
    return None


def _as_title(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        return _as_title(value.get("name") or value.get("nickname") or value.get("title"))
    return None


def _pick_generic(data: Any) -> tuple[str | None, str | None, str | None]:
    if not isinstance(data, dict):
        return None, None, None
    title = _as_title(data.get("title") or data.get("desc") or data.get("name"))
    if not title and isinstance(data.get("author"), dict):
        title = _as_title(data["author"].get("name") or data["author"].get("nickname"))
    cover_blob = data.get("cover") or data.get("cover_url") or data.get("origin_cover")
    cd = data.get("cover_data")
    if not cover_blob and isinstance(cd, dict):
        cover_blob = cd.get("cover") or cd.get("origin_cover")
    cover = _first_http(cover_blob)
    video = data.get("video") or data.get("video_data") or data.get("data")
    direct = None
    if isinstance(video, dict):
        direct = (
            _first_http(video.get("nwm_video_url_hq"))
            or _first_http(video.get("nwm_video_url"))
            or _first_http(video.get("wm_video_url"))
            or _first_http(video.get("url"))
            or _first_http(video.get("play"))
            or _first_http(video.get("src"))
            or _first_http(video.get("play_addr") or video.get("playAddr") or video.get("download_addr"))
        )
    elif isinstance(video, str):
        direct = _first_http(video)
    direct = direct or _first_http(
        data.get("nwm_video_url_hq")
        or data.get("nwm_video_url")
        or data.get("play_video")
        or data.get("video_url")
        or data.get("url")
        or data.get("play")
    )
    if not direct:
        play = _walk_http(
            data,
            pred=lambda o: isinstance(o, dict)
            and (o.get("url_list") or o.get("urlList"))
            and (o.get("uri") or o.get("url_key") or o.get("data_size")),
        )
        if play and ("play" in play or "aweme" in play or "tos" in play or ".mp4" in play):
            direct = play
    if isinstance(direct, str) and not direct.startswith("http"):
        direct = None
    return direct, title, (cover if isinstance(cover, str) else None)


def _ok(url: str, *, title: str | None, direct: str, key: str) -> dict:
    ext = "m3u8" if ".m3u8" in direct.lower() else "mp4"
    return {
        "ok": True,
        "title": title or "video",
        "ext": ext,
        "filesize": None,
        "thumbnail": None,
        "extractor": "webparser",
        "extractor_key": key,
        "platform": platform_of(url),
        "direct_url": direct,
        "needs_merge": ext == "m3u8",
        "page_url": url,
    }


def _fail(key: str, msg: str) -> dict:
    return {"ok": False, "error": f"webparser/{key}: {msg}"[:240]}


def _json_or_none(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return None


def _try_17change(url: str) -> dict:
    body = {"link": url}
    try:
        with httpx.Client(follow_redirects=True, timeout=BACKEND_TIMEOUT) as client:
            resp = client.post(PARSE_17, json=body, headers=_sign_17(body))
    except Exception as exc:
        return _fail("17change", str(exc)[:160])
    payload = _json_or_none(resp)
    log.info("webparser 17change status=%s body=%s", resp.status_code, (resp.text or "")[:240])
    if not isinstance(payload, dict):
        return _fail("17change", f"非 JSON ({resp.status_code})")
    code = payload.get("code")
    data = payload.get("data")
    if code not in (200, "200", 0, "ok", "OK"):
        msg = payload.get("message") or payload.get("msg") or f"code={code}"
        return _fail("17change", str(msg))
    direct, title, cover = _pick_generic(data if isinstance(data, dict) else payload)
    if not direct:
        return _fail("17change", "响应无视频地址")
    out = _ok(url, title=title, direct=direct, key="17change")
    if cover:
        out["thumbnail"] = cover
    return out


def _try_evil0ctal(url: str) -> dict:
    if not is_douyin(url):
        return _fail("douyin.wtf", "仅处理抖音")
    params = {"url": url, "minimal": "true"}
    headers = {"User-Agent": SITE_UA, "Accept": "application/json"}
    try:
        with httpx.Client(follow_redirects=True, timeout=BACKEND_TIMEOUT) as client:
            resp = client.get(EVIL_HYBRID, params=params, headers=headers)
    except Exception as exc:
        return _fail("douyin.wtf", str(exc)[:160])
    payload = _json_or_none(resp)
    snippet = (resp.text or "")[:240]
    log.info("webparser douyin.wtf status=%s body=%s", resp.status_code, snippet)
    if resp.status_code == 429:
        return _fail("douyin.wtf", "rate limited")
    if not isinstance(payload, dict):
        return _fail("douyin.wtf", f"非 JSON ({resp.status_code})")
    code = payload.get("code")
    if code not in (200, "200", 0, "ok", "OK", None):
        msg = payload.get("message") or payload.get("msg") or f"code={code}"
        return _fail("douyin.wtf", str(msg))
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    direct, title, cover = _pick_generic(data)
    if not direct:
        return _fail("douyin.wtf", "响应无视频地址")
    out = _ok(url, title=title, direct=direct, key="douyin.wtf")
    if cover:
        out["thumbnail"] = cover
    return out


def _try_yujn(url: str) -> dict:
    if not is_douyin(url):
        return _fail("yujn", "仅处理抖音")
    headers = {"User-Agent": SITE_UA, "Accept": "application/json"}
    try:
        with httpx.Client(follow_redirects=True, timeout=BACKEND_TIMEOUT) as client:
            resp = client.get(YUJN_DY, params={"msg": url}, headers=headers)
    except Exception as exc:
        return _fail("yujn", str(exc)[:160])
    payload = _json_or_none(resp)
    log.info("webparser yujn status=%s body=%s", resp.status_code, (resp.text or "")[:240])
    if not isinstance(payload, dict):
        return _fail("yujn", f"非 JSON ({resp.status_code})")
    direct, title, cover = _pick_generic(payload)
    direct = direct or _first_http(payload.get("play_video") or payload.get("video"))
    if not direct:
        msg = payload.get("msg") or payload.get("message") or "响应无视频地址"
        return _fail("yujn", str(msg))
    out = _ok(url, title=title or _as_title(payload.get("name")), direct=direct, key="yujn")
    if cover:
        out["thumbnail"] = cover
    return out


def _try_tenapi(url: str) -> dict:
    headers = {"User-Agent": SITE_UA}
    try:
        with httpx.Client(follow_redirects=True, timeout=BACKEND_TIMEOUT) as client:
            resp = client.post(TENAPI_V2, data={"url": url}, headers=headers)
    except Exception as exc:
        return _fail("tenapi", str(exc)[:160])
    payload = _json_or_none(resp)
    log.info("webparser tenapi status=%s body=%s", resp.status_code, (resp.text or "")[:180])
    if not isinstance(payload, dict):
        return _fail("tenapi", f"非 JSON ({resp.status_code})")
    code = payload.get("code")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if code not in (200, "200", 0, "ok", "OK", None):
        msg = payload.get("msg") or payload.get("message") or f"code={code}"
        return _fail("tenapi", str(msg))
    direct, title, cover = _pick_generic(data)
    if not direct:
        return _fail("tenapi", payload.get("msg") or "响应无视频地址")
    out = _ok(url, title=title, direct=direct, key="tenapi")
    if cover:
        out["thumbnail"] = cover
    return out


class WebParserEngine:
    name = "webparser"
    stage = 30

    def available(self) -> bool:
        return True

    def version(self) -> str:
        return "17change+douyin.wtf+yujn+tenapi"

    def matches(self, url: str) -> bool:
        # TikTok dual is not guessed from a Douyin id — only the URL host matters,
        # and this engine stays on Douyin / Kuaishou public parsers.
        host = hostname_of(url)
        if host.endswith("tiktok.com"):
            return False
        return is_douyin(url) or is_kuaishou(url)

    def extract(self, url: str) -> dict:
        backends: list[tuple[str, Any]] = [("17change", _try_17change)]
        if is_douyin(url):
            backends.append(("douyin.wtf", _try_evil0ctal))
            backends.append(("yujn", _try_yujn))
        backends.append(("tenapi", _try_tenapi))

        errors: list[str] = []
        with ThreadPoolExecutor(max_workers=len(backends)) as pool:
            futs = {pool.submit(fn, url): name for name, fn in backends}
            try:
                for fut in as_completed(futs, timeout=RACE_TIMEOUT):
                    name = futs[fut]
                    try:
                        result = fut.result()
                    except Exception as exc:
                        errors.append(f"{name}: {str(exc)[:120]}")
                        continue
                    if result and result.get("ok") and result.get("direct_url"):
                        log.info("webparser win backend=%s", result.get("extractor_key") or name)
                        for other in futs:
                            other.cancel()
                        return result
                    errors.append((result or {}).get("error") or f"{name}: 失败")
            except TimeoutError:
                errors.append("webparser: 公共解析超时")
        detail = "；".join(errors[:6]) if errors else "所有公共解析均失败"
        return {"ok": False, "error": detail[:400]}
