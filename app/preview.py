"""In-page video preview: reverse-proxy the CDN so the browser can play it."""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from .config import DOWNLOAD_TIMEOUT
from .download import _dl_headers
from .jobs import STORE
from .util import is_hls

log = logging.getLogger("unwatermark")

router = APIRouter()

_TIMEOUT = httpx.Timeout(connect=20.0, read=DOWNLOAD_TIMEOUT, write=30.0, pool=20.0)
_UNSUPPORTED = {"ok": False, "error": "该格式暂不支持预览"}


def _media_type(upstream: str | None, ext: str | None) -> str:
    ct = (upstream or "").split(";")[0].strip().lower()
    if ct.startswith("video/") or ct in {"application/octet-stream", "application/mp4"}:
        return upstream.split(";")[0].strip() if upstream else "video/mp4"
    ext = (ext or "").lower().lstrip(".")
    if ext in {"webm"}:
        return "video/webm"
    if ext in {"mov", "qt"}:
        return "video/quicktime"
    if ext in {"m4v"}:
        return "video/x-m4v"
    return "video/mp4"


@router.api_route("/api/preview", methods=["GET", "HEAD"])
async def preview(request: Request, job: str = Query(..., min_length=8, max_length=64)):
    item = STORE.get(job)
    if item is None:
        raise HTTPException(404, "任务不存在或已过期，请重新解析")
    if not item.direct_url or not item.direct_url.startswith("http") or is_hls(item.direct_url):
        return JSONResponse(_UNSUPPORTED, status_code=415)

    headers = _dl_headers(item.direct_url, item.page_url)
    rng = request.headers.get("range")
    if rng:
        headers["Range"] = rng

    client = httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT)
    try:
        req = client.build_request("GET", item.direct_url, headers=headers)
        resp = await client.send(req, stream=True)
    except Exception as exc:
        await client.aclose()
        log.warning("preview upstream open failed job=%s err=%s", job, exc)
        raise HTTPException(502, "预览失败") from exc

    if resp.status_code >= 400:
        await resp.aclose()
        await client.aclose()
        log.warning("preview upstream status=%s job=%s", resp.status_code, job)
        raise HTTPException(502, "预览失败")

    status = 206 if resp.status_code == 206 else 200
    media = _media_type(resp.headers.get("content-type"), item.ext)
    out = {
        "Accept-Ranges": resp.headers.get("accept-ranges") or "bytes",
        "Content-Disposition": "inline",
        "Cache-Control": "no-store",
    }
    if resp.headers.get("content-range"):
        out["Content-Range"] = resp.headers["content-range"]
    if resp.headers.get("content-length"):
        out["Content-Length"] = resp.headers["content-length"]

    if request.method == "HEAD":
        await resp.aclose()
        await client.aclose()
        return Response(status_code=status, media_type=media, headers=out)

    async def body():
        try:
            async for chunk in resp.aiter_bytes(64 * 1024):
                yield chunk
        finally:
            await resp.aclose()
            await client.aclose()

    return StreamingResponse(body(), status_code=status, media_type=media, headers=out)
