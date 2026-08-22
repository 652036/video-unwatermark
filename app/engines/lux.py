"""lux CLI engine (release binary only — never a git clone)."""

from __future__ import annotations

import json
import os
import subprocess
import tarfile
from pathlib import Path

import httpx

from ..config import ROOT
from ..urls import is_douyin, is_kuaishou
from ..util import platform_of

LUX_BIN = ROOT / "bin" / "lux"
LUX_ASSET = "https://github.com/iawia002/lux/releases/download/v0.24.1/lux_0.24.1_Linux_x86_64.tar.gz"
_ENSURED = False


def _ensure_lux() -> bool:
    global _ENSURED
    if LUX_BIN.is_file() and os.access(LUX_BIN, os.X_OK):
        return True
    if _ENSURED:
        return LUX_BIN.is_file()
    _ENSURED = True
    try:
        LUX_BIN.parent.mkdir(parents=True, exist_ok=True)
        tmp = LUX_BIN.parent / ".lux.tgz"
        with httpx.Client(follow_redirects=True, timeout=40.0) as client:
            resp = client.get(LUX_ASSET)
            resp.raise_for_status()
            tmp.write_bytes(resp.content)
        with tarfile.open(tmp, "r:gz") as tf:
            member = next((m for m in tf.getmembers() if Path(m.name).name == "lux" and m.isfile()), None)
            if member is None:
                return False
            member.name = "lux"
            tf.extract(member, path=str(LUX_BIN.parent))
        tmp.unlink(missing_ok=True)
        LUX_BIN.chmod(0o755)
        return LUX_BIN.is_file()
    except Exception:
        return False


def _pick_stream(data: dict) -> tuple[str | None, str, int | None]:
    streams = data.get("streams") or data.get("Stream") or {}
    if not isinstance(streams, dict):
        return None, "mp4", None
    best_url = None
    best_ext = "mp4"
    best_size = -1
    for val in streams.values():
        if not isinstance(val, dict):
            continue
        size = val.get("size") or val.get("Size") or 0
        try:
            size = int(size)
        except Exception:
            size = 0
        ext = str(val.get("ext") or val.get("Ext") or "mp4").lstrip(".")
        url = None
        urls = val.get("urls") or val.get("url") or val.get("URL")
        if isinstance(urls, str):
            url = urls
        elif isinstance(urls, list) and urls:
            first = urls[0]
            if isinstance(first, str):
                url = first
            elif isinstance(first, dict):
                url = first.get("url") or first.get("URL")
        if url and size >= best_size:
            best_url, best_ext, best_size = url, ext or "mp4", size
    return best_url, best_ext, (best_size if best_size > 0 else None)


class LuxEngine:
    name = "lux"
    stage = 30

    def available(self) -> bool:
        return _ensure_lux()

    def version(self) -> str:
        if not LUX_BIN.is_file():
            return "missing"
        try:
            proc = subprocess.run([str(LUX_BIN), "-v"], capture_output=True, text=True, timeout=5)
            line = (proc.stdout or proc.stderr or "").strip().splitlines()
            return (line[0] if line else "0.24.1")[:80]
        except Exception:
            return "0.24.1"

    def matches(self, url: str) -> bool:
        return is_douyin(url) or is_kuaishou(url)

    def extract(self, url: str) -> dict:
        if not _ensure_lux():
            return {"ok": False, "error": "lux 二进制不可用"}
        try:
            proc = subprocess.run(
                [str(LUX_BIN), "-j", "-s", url],
                capture_output=True,
                text=True,
                timeout=20,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "lux 超时"}
        except Exception as exc:
            return {"ok": False, "error": f"lux: {str(exc)[:160]}"}
        blob = (proc.stdout or "").strip()
        if not blob:
            err = (proc.stderr or "lux 无输出").strip().splitlines()
            return {"ok": False, "error": (err[-1] if err else "lux 无输出")[:240]}
        data = None
        for candidate in (blob, blob[blob.find("{") :] if "{" in blob else "", blob[blob.find("[") :] if "[" in blob else ""):
            if not candidate:
                continue
            try:
                data = json.loads(candidate)
                break
            except json.JSONDecodeError:
                continue
        if isinstance(data, list) and data:
            data = data[0]
        if not isinstance(data, dict):
            return {"ok": False, "error": "lux 无法解析 JSON"}
        if data.get("err"):
            return {"ok": False, "error": str(data.get("err"))[:240]}
        direct, ext, size = _pick_stream(data)
        if not direct:
            return {"ok": False, "error": "lux 未找到媒体流"}
        title = data.get("title") or data.get("Title") or "video"
        site = data.get("site") or data.get("Site") or "lux"
        return {
            "ok": True,
            "title": title,
            "ext": ext or "mp4",
            "filesize": size,
            "thumbnail": None,
            "extractor": self.name,
            "extractor_key": str(site),
            "platform": platform_of(url, str(site)),
            "direct_url": direct,
            "needs_merge": False,
            "page_url": url,
        }
