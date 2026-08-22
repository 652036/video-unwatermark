"""you-get engine via --json (pip-installable CN/intl parser)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from ..cookies import current
from ..util import looks_like_login_error, platform_of

VIDEO_EXTS = {"mp4", "webm", "mkv", "mov", "flv", "ts", "m4a", "m4v", "ogg", "ogv"}


def _youget_bin() -> list[str]:
    exe = shutil.which("you-get")
    if exe:
        return [exe]
    return [sys.executable, "-m", "you_get"]


def _cookie_args() -> list[str]:
    opts = current()
    if opts.cookiefile:
        return ["-c", opts.cookiefile]
    return []


def _clean_err(text: str) -> str:
    lines = []
    for line in (text or "").splitlines():
        if "RuntimeWarning" in line or "sys.modules" in line or line.startswith("  "):
            continue
        lines.append(line)
    return " ".join(lines).strip()[:240]


class YouGetEngine:
    stage = 20
    name = "you-get"

    def available(self) -> bool:
        try:
            import you_get  # noqa: F401

            return True
        except Exception:
            return False

    def version(self) -> str:
        try:
            import you_get

            ver = getattr(you_get, "__version__", None)
            if ver:
                return str(ver)
        except Exception:
            pass
        return "0.4.1743"

    def extract(self, url: str) -> dict:
        try:
            proc = subprocess.run(
                [*_youget_bin(), *_cookie_args(), "--json", url],
                capture_output=True,
                text=True,
                timeout=24,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "you-get 超时"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:240]}

        blob = (proc.stdout or "").strip()
        if not blob:
            err = _clean_err(proc.stderr) or "you-get 无输出"
            if looks_like_login_error(err):
                return {"ok": False, "error": "needs cookie", "needs_cookie": True}
            return {"ok": False, "error": err}

        data = None
        for candidate in (blob, blob[blob.find("{") :] if "{" in blob else ""):
            if not candidate:
                continue
            try:
                data = json.loads(candidate)
                break
            except json.JSONDecodeError:
                continue
        if not isinstance(data, dict):
            err = _clean_err(proc.stderr) or "you-get 无法解析 JSON"
            if looks_like_login_error(err):
                return {"ok": False, "error": "needs cookie", "needs_cookie": True}
            return {"ok": False, "error": err}

        title = data.get("title") or "video"
        streams = data.get("streams") or {}
        best = _pick_stream(streams)
        if not best:
            return {"ok": False, "error": "you-get 未找到媒体流"}
        src = best.get("src") or []
        if isinstance(src, str):
            src = [src]
        direct = src[0] if src else None
        ext = str(best.get("container") or "mp4").lstrip(".").lower()
        if ext not in VIDEO_EXTS:
            return {"ok": False, "error": f"you-get 未找到视频流（得到 {ext}）"}
        size = best.get("size")
        site = data.get("site") or data.get("extractor")
        return {
            "ok": True,
            "title": title,
            "ext": ext,
            "filesize": int(size) if size else None,
            "thumbnail": None,
            "extractor": self.name,
            "extractor_key": site,
            "platform": platform_of(url, site),
            "direct_url": direct,
            "needs_merge": len(src) > 1 or not direct,
            "page_url": url,
        }

    def download_to(self, url: str, dest_dir: str, filename: str) -> str | None:
        proc = subprocess.run(
            [*_youget_bin(), *_cookie_args(), "-o", dest_dir, "-O", filename, url],
            capture_output=True,
            text=True,
            timeout=170,
        )
        if proc.returncode != 0:
            return None
        folder = Path(dest_dir)
        matches = sorted(folder.glob(filename + ".*"), key=lambda p: p.stat().st_mtime, reverse=True)
        return str(matches[0]) if matches else None


def _pick_stream(streams: dict) -> dict | None:
    if not streams:
        return None
    scored = []
    for key, val in streams.items():
        if not isinstance(val, dict):
            continue
        ext = str(val.get("container") or "").lstrip(".").lower()
        if ext and ext not in VIDEO_EXTS:
            continue
        size = val.get("size") or 0
        scored.append((size, key, val))
    if not scored:
        return None
    scored.sort(reverse=True)
    return scored[0][2]
