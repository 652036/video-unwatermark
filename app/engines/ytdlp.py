"""yt-dlp engine (required). Prefer watermark-free formats for TikTok/Douyin."""

from __future__ import annotations

from urllib.parse import urlparse

import yt_dlp

from ..config import UA
from ..cookies import current, ytdlp_cookie_opts
from ..util import looks_like_login_error, platform_of


def _format_for(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if "tiktok.com" in host or "douyin.com" in host or "iesdouyin.com" in host:
        # 'download' is the classic no-watermark TikTok format id
        return "download/best[format_note!*=watermark]/bv*+ba/b"
    return "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/best"


def _ydl_opts(url: str, *, download: bool = False, outtmpl: str | None = None) -> dict:
    opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "skip_download": not download,
        "format": _format_for(url),
        "merge_output_format": "mp4",
        "socket_timeout": 15,
        "retries": 2,
        "http_headers": {"User-Agent": UA},
        "cachedir": False,
        "extractor_args": {"twitter": {"api": ["syndication", "legacy"]}},
    }
    cookie_opts = ytdlp_cookie_opts(current())
    opts.update(cookie_opts)
    # Logged-in / cookie path: Vimeo anonymous macos OAuth is dead; web client needs cookies.
    if cookie_opts:
        args = dict(opts.get("extractor_args") or {})
        args.setdefault("vimeo", {})
        args["vimeo"] = dict(args.get("vimeo") or {})
        args["vimeo"].setdefault("client", ["web"])
        opts["extractor_args"] = args
    if outtmpl:
        opts["outtmpl"] = outtmpl
        opts["restrictfilenames"] = False
    return opts


class YtDlpEngine:
    stage = 20
    name = "yt-dlp"

    def available(self) -> bool:
        return True

    def version(self) -> str:
        return getattr(yt_dlp.version, "__version__", "unknown")

    def extract(self, url: str) -> dict:
        try:
            with yt_dlp.YoutubeDL(_ydl_opts(url)) as ydl:
                info = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as exc:
            msg = str(exc)
            if looks_like_login_error(msg):
                return {"ok": False, "error": "needs cookie", "needs_cookie": True}
            return {"ok": False, "error": _short_err(msg)}
        except Exception as exc:
            msg = str(exc)
            if looks_like_login_error(msg):
                return {"ok": False, "error": "needs cookie", "needs_cookie": True}
            return {"ok": False, "error": _short_err(msg)}

        if not info:
            return {"ok": False, "error": "yt-dlp 未返回信息"}
        if info.get("_type") == "playlist" and info.get("entries"):
            info = info["entries"][0] or {}

        requested = info.get("requested_downloads") or []
        fmt = requested[0] if requested else info
        direct = fmt.get("url") or info.get("url")
        ext = (fmt.get("ext") or info.get("ext") or "mp4").lstrip(".")
        filesize = fmt.get("filesize") or fmt.get("filesize_approx") or info.get("filesize")
        vcodec = fmt.get("vcodec")
        acodec = fmt.get("acodec")
        needs_merge = bool(
            (not direct)
            or (vcodec and vcodec != "none" and acodec == "none")
            or (acodec and acodec != "none" and vcodec == "none")
        )
        ie = info.get("extractor_key") or info.get("ie_key") or info.get("extractor") or "yt-dlp"
        title = info.get("title") or info.get("fulltitle") or "video"
        thumb = info.get("thumbnail")
        if not thumb and info.get("thumbnails"):
            thumb = (info["thumbnails"][-1] or {}).get("url")
        if not direct and not info.get("formats"):
            return {"ok": False, "error": "未找到可下载的媒体"}
        return {
            "ok": True,
            "title": title,
            "ext": ext or "mp4",
            "filesize": int(filesize) if filesize else None,
            "thumbnail": thumb,
            "extractor": self.name,
            "extractor_key": ie,
            "platform": platform_of(url, ie),
            "direct_url": direct,
            "needs_merge": needs_merge,
            "page_url": url,
        }

    def download_to(self, url: str, outtmpl: str) -> str | None:
        opts = _ydl_opts(url, download=True, outtmpl=outtmpl)
        opts["skip_download"] = False
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return None
            path = info.get("requested_downloads", [{}])[0].get("filepath") or info.get("_filename")
            if path:
                return path
            prepared = ydl.prepare_filename(info)
            return prepared


def _short_err(msg: str) -> str:
    line = msg.strip().splitlines()[-1] if msg.strip() else "yt-dlp 解析失败"
    if "ERROR:" in line:
        line = line.split("ERROR:", 1)[-1].strip()
    return line[:240]
