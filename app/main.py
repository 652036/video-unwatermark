"""FastAPI entry: parse / download / health."""

from __future__ import annotations

import logging
import shutil
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import BROWSER_CHOICES, STATIC_DIR
from .cookies import (
    CookieOpts,
    cookie_scope,
    current,
    resolve_local_path,
    save_uploaded_cookies,
    validate_browser,
)
from .download import materialize
from .extract import engines_status, extract_media, normalize_input
from .jobs import STORE
from .preview import router as preview_router
from .util import hostname_of, sanitize_filename

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("unwatermark")

app = FastAPI(title="视频无水印解析", version="1.1.0", docs_url="/api/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(preview_router)


class ParseBody(BaseModel):
    url: str = Field(..., min_length=1, max_length=8000)
    cookies_from_browser: str | None = Field(default=None, max_length=80)
    cookies_path: str | None = Field(default=None, max_length=512)


def _empty_fail(error: str, *, needs_cookie: bool = False, hint: str | None = None, platform=None):
    body = {
        "ok": False,
        "error": error,
        "needs_cookie": needs_cookie,
        "title": None,
        "ext": None,
        "filesize": None,
        "thumbnail": None,
        "extractor": None,
        "platform": platform,
        "download_url": None,
        "direct_url": None,
        "preview_url": None,
    }
    if hint:
        body["hint"] = hint
    return JSONResponse(body)


def _merge_cookie_opts(
    *,
    cookies_from_browser: str | None,
    cookies_path: str | None,
    uploaded: str | None,
) -> CookieOpts:
    env = CookieOpts.from_env()
    browser = (cookies_from_browser or "").strip() or env.cookies_from_browser
    if browser:
        err = validate_browser(browser)
        if err:
            raise ValueError(err)
    path = uploaded or cookies_path or env.cookiefile
    if cookies_path and not uploaded:
        path = resolve_local_path(cookies_path)
    return CookieOpts(cookiefile=path, cookies_from_browser=browser)


async def _parse_core(url_text: str, opts: CookieOpts):
    url, err = normalize_input(url_text)
    if err:
        return _empty_fail(err)
    with cookie_scope(opts):
        result = await extract_media(url)
    if not result.get("ok"):
        return _empty_fail(
            result.get("error") or "解析失败",
            needs_cookie=bool(result.get("needs_cookie")),
            hint=result.get("hint"),
            platform=result.get("platform"),
        )
    job = STORE.create(
        page_url=url,
        title=result.get("title") or "video",
        ext=result.get("ext") or "mp4",
        filesize=result.get("filesize"),
        thumbnail=result.get("thumbnail"),
        extractor=result.get("extractor") or "yt-dlp",
        platform=result.get("platform") or hostname_of(url),
        direct_url=result.get("direct_url"),
        needs_merge=bool(result.get("needs_merge")),
        extra={
            "cookiefile": opts.cookiefile,
            "cookies_from_browser": opts.cookies_from_browser,
        },
    )
    return {
        "ok": True,
        "title": job.title,
        "ext": job.ext,
        "filesize": job.filesize,
        "thumbnail": job.thumbnail,
        "extractor": job.extractor,
        "platform": job.platform,
        "download_url": f"/api/download?job={job.id}",
        "direct_url": job.direct_url,
        "preview_url": f"/api/preview?job={job.id}",
        "job": job.id,
    }


@app.get("/api/health")
async def health():
    env = CookieOpts.from_env()
    return {
        "ok": True,
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "engines": engines_status(),
        "cookies": {
            "file_configured": bool(env.cookiefile),
            "browser_configured": bool(env.cookies_from_browser),
            "browsers": list(BROWSER_CHOICES),
        },
    }


@app.get("/api/engines")
async def engines():
    return {"engines": engines_status()}


@app.post("/api/parse")
async def parse(request: Request):
    ctype = (request.headers.get("content-type") or "").lower()
    try:
        if "multipart/form-data" in ctype:
            form = await request.form()
            url_text = str(form.get("url") or "")
            browser = str(form.get("cookies_from_browser") or "") or None
            path = str(form.get("cookies_path") or "") or None
            uploaded_path = None
            upload = form.get("cookies_file")
            if upload is not None and hasattr(upload, "read"):
                data = await upload.read()
                if data:
                    uploaded_path = save_uploaded_cookies(data)
            opts = _merge_cookie_opts(
                cookies_from_browser=browser, cookies_path=path, uploaded=uploaded_path
            )
            return await _parse_core(url_text, opts)
        body = ParseBody.model_validate(await request.json())
        opts = _merge_cookie_opts(
            cookies_from_browser=body.cookies_from_browser,
            cookies_path=body.cookies_path,
            uploaded=None,
        )
        return await _parse_core(body.url, opts)
    except ValueError as exc:
        return _empty_fail(str(exc))


@app.get("/api/download")
async def download(job: str = Query(..., min_length=8, max_length=64)):
    item = STORE.get(job)
    if item is None:
        raise HTTPException(404, "任务不存在或已过期，请重新解析")
    extra = item.extra or {}
    opts = CookieOpts(
        cookiefile=extra.get("cookiefile"),
        cookies_from_browser=extra.get("cookies_from_browser"),
    )
    if not opts.configured():
        opts = current()
    try:
        with cookie_scope(opts):
            path = materialize(item)
    except Exception as exc:
        raise HTTPException(502, f"下载失败：{exc}") from exc
    filename = sanitize_filename(item.title) + "." + (path.suffix.lstrip(".") or item.ext or "mp4")
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
    }
    media = "video/mp4" if path.suffix.lower() in {".mp4", ".m4v"} else "application/octet-stream"
    return FileResponse(path, media_type=media, filename=filename, headers=headers)


@app.get("/")
async def index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.is_file():
        raise HTTPException(500, "前端未找到")
    return FileResponse(index_file)


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
