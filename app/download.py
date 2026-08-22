"""Download a parsed job to disk, then stream it."""

from __future__ import annotations

import logging
from pathlib import Path

from .config import DOWNLOAD_DIR, DOWNLOAD_TIMEOUT, MAX_DOWNLOAD_BYTES, MOBILE_UA, UA
from .engines.ytdlp import YtDlpEngine
from .jobs import Job, STORE
from .util import hostname_of, is_hls, sanitize_filename

log = logging.getLogger("unwatermark")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def materialize(job: Job) -> Path:
    if job.filepath and Path(job.filepath).is_file() and Path(job.filepath).stat().st_size > 0:
        return Path(job.filepath)

    stem = sanitize_filename(job.title or "video") + "_" + job.id[:8]
    outtmpl = str(DOWNLOAD_DIR / (stem + ".%(ext)s"))

    path: Path | None = None
    engine = (job.extractor or "yt-dlp").lower()
    if engine == "yt-dlp" or job.needs_merge or is_hls(job.direct_url):
        ydl = YtDlpEngine()
        raw = ydl.download_to(job.page_url, outtmpl)
        if raw:
            path = Path(raw)
    elif engine == "videofetch":
        from .engines.videofetch_engine import VideofetchEngine

        raw = VideofetchEngine().download_to(job.page_url, str(DOWNLOAD_DIR))
        if raw:
            path = Path(raw)
    elif engine == "you-get":
        from .engines.youget import YouGetEngine

        raw = YouGetEngine().download_to(job.page_url, str(DOWNLOAD_DIR), stem)
        if raw:
            path = Path(raw)

    if path is None and job.direct_url and job.direct_url.startswith("http") and not is_hls(job.direct_url):
        path = _http_download(job.direct_url, DOWNLOAD_DIR / f"{stem}.{job.ext or 'mp4'}", page_url=job.page_url)

    if path is None or not path.is_file():
        # last resort: yt-dlp on the original page
        raw = YtDlpEngine().download_to(job.page_url, outtmpl)
        if raw:
            path = Path(raw)

    if path is None or not path.is_file():
        raise RuntimeError("下载失败")
    if path.stat().st_size > MAX_DOWNLOAD_BYTES:
        path.unlink(missing_ok=True)
        raise RuntimeError("文件过大，已取消")
    STORE.set_path(job.id, path)
    log.info("download job=%s size=%s", job.id, path.stat().st_size)
    return path


def _http_download(url: str, dest: Path, page_url: str | None = None) -> Path | None:
    try:
        import httpx
    except Exception:
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with httpx.Client(follow_redirects=True, timeout=DOWNLOAD_TIMEOUT, headers=_dl_headers(url, page_url)) as client:
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                written = 0
                with tmp.open("wb") as fh:
                    for chunk in resp.iter_bytes(1024 * 64):
                        written += len(chunk)
                        if written > MAX_DOWNLOAD_BYTES:
                            raise RuntimeError("文件过大")
                        fh.write(chunk)
        tmp.replace(dest)
        return dest
    except Exception:
        tmp.unlink(missing_ok=True)
        return None


def _dl_headers(url: str, page_url: str | None = None) -> dict[str, str]:
    """Headers CDNs expect for Douyin/Kuaishou progressive MP4."""
    blob = " ".join(x for x in (url, page_url) if x).lower()
    host = hostname_of(page_url or "") or hostname_of(url)
    if any(k in blob for k in ("kuaishou", "chenzhongtech", "kwai.com", "gifshow")):
        referer = "https://www.kuaishou.com/"
    elif "iesdouyin" in blob:
        referer = "https://www.iesdouyin.com/"
    elif "douyin" in blob:
        referer = "https://www.douyin.com/"
    elif host:
        referer = f"https://{host}/"
    else:
        referer = "https://www.douyin.com/"
    return {
        "User-Agent": MOBILE_UA,
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": referer,
    }

