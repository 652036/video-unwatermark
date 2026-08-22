"""videofetch / videodl engine. Restricted to public UGC clients only."""

from __future__ import annotations

from ..config import DOWNLOAD_DIR, VIDEOFETCH_ALLOW
from ..cookies import current, httpx_cookie_dict
from ..urls import is_kuaishou, ytdlp_url
from ..util import looks_like_login_error, platform_of

_CLIENT = None
_IMPORT_ERROR = None

try:
    from videodl.videodl import VideoClient
except Exception as exc:  # pragma: no cover
    VideoClient = None  # type: ignore
    _IMPORT_ERROR = exc


def _client():
    global _CLIENT
    if _CLIENT is None:
        if VideoClient is None:
            raise RuntimeError(f"videofetch 不可用: {_IMPORT_ERROR}")
        init_cfg = {
            name: {
                "disable_print": True,
                "work_dir": str(DOWNLOAD_DIR),
                "max_retries": 2,
            }
            for name in VIDEOFETCH_ALLOW
        }
        _CLIENT = VideoClient(
            allowed_video_sources=list(VIDEOFETCH_ALLOW),
            init_video_clients_cfg=init_cfg,
        )
    return _CLIENT


def _overrides() -> dict:
    cookies = httpx_cookie_dict(current())
    if cookies:
        return {"cookies": cookies}
    return {}


class VideofetchEngine:
    stage = 20
    name = "videofetch"

    def available(self) -> bool:
        return VideoClient is not None

    def version(self) -> str:
        try:
            import videodl

            return getattr(videodl, "__version__", "0.9.1")
        except Exception:
            return "0.9.1"

    def extract(self, url: str) -> dict:
        try:
            if is_kuaishou(url):
                infos = self._kuaishou_requests(url)
            else:
                # VideoClient.parsefromurl(url) does not accept request_overrides.
                infos = _client().parsefromurl(url)
        except Exception as exc:
            msg = str(exc)
            if looks_like_login_error(msg):
                return {"ok": False, "error": "needs cookie", "needs_cookie": True}
            return {"ok": False, "error": (msg or "videofetch 解析失败")[:240]}

        if not infos:
            return {"ok": False, "error": "videofetch 未返回结果"}

        info = None
        for item in infos:
            if getattr(item, "err_msg", None) and looks_like_login_error(item.err_msg):
                return {"ok": False, "error": "needs cookie", "needs_cookie": True}
            if getattr(item, "with_valid_download_url", False):
                info = item
                break
        if info is None:
            err = getattr(infos[0], "err_msg", "") or "videofetch 未找到直链"
            if looks_like_login_error(err):
                return {"ok": False, "error": "needs cookie", "needs_cookie": True}
            return {"ok": False, "error": str(err)[:240]}

        source = str(getattr(info, "source", "") or "videofetch")
        title = getattr(info, "title", "") or "video"
        ext = (getattr(info, "ext", None) or "mp4").lstrip(".")
        direct = getattr(info, "download_url", None)
        if direct is not None and not isinstance(direct, str):
            direct_url = None
            needs_merge = True
        else:
            direct_url = direct or None
            needs_merge = not bool(direct_url)
        thumb = getattr(info, "cover_url", None)
        return {
            "ok": True,
            "title": title,
            "ext": ext or "mp4",
            "filesize": None,
            "thumbnail": thumb if isinstance(thumb, str) else None,
            "extractor": self.name,
            "extractor_key": source,
            "platform": platform_of(url, source.replace("VideoClient", "")),
            "direct_url": direct_url,
            "needs_merge": needs_merge,
            "page_url": url,
        }

    def _kuaishou_requests(self, url: str):
        """Skip DrissionPage (headless) — it is what timed out in smoke tests."""
        from videodl.modules.sources.kuaishou import KuaishouVideoClient

        page = ytdlp_url(url)
        ks = KuaishouVideoClient(
            disable_print=True,
            work_dir=str(DOWNLOAD_DIR),
            max_retries=2,
        )
        return ks._parsefromurlusingrequests(page, request_overrides=_overrides() or None)

    def download_to(self, url: str, dest_dir: str) -> str | None:
        if is_kuaishou(url):
            infos = self._kuaishou_requests(url)
            if not infos:
                return None
            from videodl.modules.sources.kuaishou import KuaishouVideoClient

            ks = KuaishouVideoClient(disable_print=True, work_dir=dest_dir, max_retries=2)
            ks.download(infos)
            for info in infos:
                path = getattr(info, "save_path", None)
                if path:
                    return str(path)
            return None
        client = _client()
        infos = client.parsefromurl(url)
        if not infos:
            return None
        client.download(infos)
        for info in infos:
            path = getattr(info, "save_path", None)
            if path:
                return str(path)
        return None
