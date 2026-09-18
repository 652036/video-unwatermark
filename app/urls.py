"""Expand share short-links and build Douyin / Kuaishou URL variants."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

import httpx

from .config import MOBILE_UA, UA
from .util import hostname_of

AWEME_RE = re.compile(
    r"/(?:share/)?(?:video|note|slides)/(\d+)|modal_id=(\d+)|aweme_id=(\d+)",
    re.I,
)
PHOTO_RE = re.compile(
    r"/(?:short-video|fw/photo|photo|f)/([A-Za-z0-9_-]+)|[?&]photoId=([A-Za-z0-9_-]+)",
    re.I,
)


def is_douyin(url: str) -> bool:
    host = hostname_of(url)
    return any(
        host == suffix or host.endswith("." + suffix)
        for suffix in ("douyin.com", "iesdouyin.com")
    )


def is_kuaishou(url: str) -> bool:
    host = hostname_of(url)
    return any(
        host == s or host.endswith("." + s)
        for s in ("kuaishou.com", "kuaishouapp.com", "chenzhongtech.com", "kwai.com", "gifshow.com")
    )


def is_cn_short_video(url: str) -> bool:
    return is_douyin(url) or is_kuaishou(url)


def aweme_id_of(url: str) -> str | None:
    m = AWEME_RE.search(url or "")
    if not m:
        return None
    return next((g for g in m.groups() if g), None)


def photo_id_of(url: str) -> str | None:
    m = PHOTO_RE.search(url or "")
    if not m:
        return None
    return next((g for g in m.groups() if g), None)


def _follow(url: str, ua: str, timeout: float = 10.0) -> str:
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout, headers={"User-Agent": ua}) as client:
            resp = client.get(url)
            return str(resp.url) or url
    except Exception:
        return url


def expand_share_url(url: str) -> str:
    """Follow v.douyin.com / v.kuaishou.com redirects. Safe no-op on failure."""
    host = hostname_of(url)
    if host in {"v.douyin.com", "www.iesdouyin.com"} or host.startswith("v."):
        followed = _follow(url, MOBILE_UA if is_douyin(url) else UA)
        if followed:
            url = followed
    if is_kuaishou(url):
        pid = photo_id_of(url)
        if pid and ("chenzhongtech.com" in hostname_of(url) or hostname_of(url).startswith("v.")):
            return f"https://www.kuaishou.com/short-video/{pid}"
    if is_douyin(url):
        aid = aweme_id_of(url)
        if aid and "iesdouyin.com" in hostname_of(url):
            return f"https://www.iesdouyin.com/share/video/{aid}"
    return url


def variants_for(url: str) -> list[str]:
    """URL shapes worth trying. First item is the preferred guest-parse target."""
    expanded = expand_share_url(url)
    out: list[str] = []

    def add(u: str | None) -> None:
        if u and u not in out:
            out.append(u)

    add(url)
    add(expanded)
    if is_douyin(url) or is_douyin(expanded):
        aid = aweme_id_of(expanded) or aweme_id_of(url)
        if aid:
            add(f"https://www.iesdouyin.com/share/video/{aid}")
            add(f"https://www.iesdouyin.com/share/note/{aid}")
            add(f"https://www.douyin.com/video/{aid}")
    if is_kuaishou(url) or is_kuaishou(expanded):
        pid = photo_id_of(expanded) or photo_id_of(url)
        if pid:
            add(f"https://www.kuaishou.com/short-video/{pid}")
            add(f"https://v.m.chenzhongtech.com/fw/photo/{pid}")
    return out or [url]


def ytdlp_url(url: str, expanded: str | None = None) -> str:
    """yt-dlp DouyinIE only matches www.douyin.com/video/<id>."""
    expanded = expanded or url
    if is_douyin(url) or is_douyin(expanded):
        aid = aweme_id_of(expanded) or aweme_id_of(url)
        if aid:
            return f"https://www.douyin.com/video/{aid}"
    if is_kuaishou(url) or is_kuaishou(expanded):
        pid = photo_id_of(expanded or url)
        if pid:
            return f"https://www.kuaishou.com/short-video/{pid}"
    return expanded or url
