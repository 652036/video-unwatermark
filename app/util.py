"""Helpers: URL extract, blocklist, filename sanitize, logging-safe host."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from .config import BLOCKED_HOSTS, PLATFORM_HINTS, WECHAT_CHANNELS_HINTS

URL_RE = re.compile(r"https?://[^\s<>\"'`]+", re.IGNORECASE)
TRAIL_PUNCT = ".,;:!?)]}>\"'`，。；：！？、）】」』》…"


def extract_url(text: str) -> str | None:
    if not text:
        return None
    raw = text.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        # still strip trailing junk from a bare URL
        return _clean_url(raw.split()[0])
    m = URL_RE.search(raw)
    if not m:
        return None
    return _clean_url(m.group(0))


def _clean_url(url: str) -> str:
    # Decoding an entire URL changes reserved delimiters and signed payloads.
    # Remove surrounding share-text punctuation without touching percent escapes.
    url = url.strip()
    url = url.rstrip(TRAIL_PUNCT)
    # chinese share links sometimes wrap the URL in extra full-width slash
    url = url.rstrip("/").rstrip(TRAIL_PUNCT)
    if "://" in url:
        scheme, rest = url.split("://", 1)
        url = scheme + "://" + rest
    return url


def hostname_of(url: str) -> str:
    try:
        host = (urlparse(url).hostname or "").lower().rstrip(".")
    except Exception:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def is_blocked(url: str) -> str | None:
    lowered = url.lower()
    for hint in WECHAT_CHANNELS_HINTS:
        if hint in lowered:
            return "微信视频号（不支持登录抓取 / MITM）"
    host = hostname_of(url)
    if not host:
        return None
    for suffix, name in BLOCKED_HOSTS.items():
        if host == suffix or host.endswith("." + suffix):
            return name
    # amazon prime video paths
    if host.endswith("amazon.com") and any(
        p in lowered for p in ("/prime", "/gp/video", "/amazonvideo")
    ):
        return "Prime Video"
    return None


def platform_of(url: str, extractor_key: str | None = None) -> str:
    host = hostname_of(url)
    for suffix, name in PLATFORM_HINTS:
        if host == suffix or host.endswith("." + suffix):
            return name
    if extractor_key:
        mapping = {
            "Youtube": "YouTube",
            "Douyin": "抖音",
            "TikTok": "TikTok",
            "BiliBili": "哔哩哔哩",
            "Kuaishou": "快手",
            "XiaoHongShu": "小红书",
            "Weibo": "微博",
            "Instagram": "Instagram",
            "Twitter": "X",
            "Facebook": "Facebook",
            "Reddit": "Reddit",
            "Vimeo": "Vimeo",
        }
        return mapping.get(extractor_key, extractor_key)
    return host or "未知"


def sanitize_filename(name: str, fallback: str = "video") -> str:
    name = (name or "").strip()
    name = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    if not name:
        name = fallback
    return name[:180]


def looks_like_login_error(msg: str) -> bool:
    text = (msg or "").lower()
    keys = (
        "sign in",
        "login required",
        "log in",
        "cookies",
        "cookie",
        "authentication",
        "private video",
        "login",
        "登录",
        "cookie",
        "需要登录",
    )
    return any(k in text for k in keys)


def is_hls(url: str | None) -> bool:
    if not url:
        return False
    u = url.lower()
    return ".m3u8" in u or "m3u8" in u.split("?")[0]
