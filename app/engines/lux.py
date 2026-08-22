"""lux CLI engine (release binary only — never a git clone)."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import httpx

from ..config import ROOT
from ..urls import is_douyin, is_kuaishou
from ..util import platform_of

LUX_VERSION = "0.24.1"
LUX_RELEASE_BASE = f"https://github.com/iawia002/lux/releases/download/v{LUX_VERSION}"

_ENSURED = False


def lux_bin_name() -> str:
    return "lux.exe" if sys.platform == "win32" else "lux"


def lux_bin_path() -> Path:
    return ROOT / "bin" / lux_bin_name()


# Module-level path used by the engine; recomputed for the current OS.
LUX_BIN = lux_bin_path()


def resolve_lux_asset(
    system: str | None = None,
    machine: str | None = None,
) -> tuple[str, str]:
    """Map OS/arch to lux release (asset_name, download_url).

    Asset names match iawia002/lux v0.24.1 goreleaser uploads, e.g.
    lux_0.24.1_Linux_x86_64.tar.gz / lux_0.24.1_Windows_x86_64.zip.
    """
    system = (system or platform.system()).strip()
    machine = (machine or platform.machine()).strip().lower()

    if system == "Darwin":
        goos = "Darwin"
    elif system == "Windows":
        goos = "Windows"
    else:
        # Linux and unknown Unix-likes: prefer Linux assets.
        goos = "Linux"

    if machine in ("x86_64", "amd64", "x64"):
        goarch = "x86_64"
    elif machine in ("aarch64", "arm64"):
        goarch = "arm64"
    elif machine in ("i386", "i686", "x86"):
        goarch = "i386"
    elif machine.startswith("armv6") or machine in ("armv6l", "arm"):
        # Windows/Linux armv6 assets exist; Darwin does not — fall back below.
        goarch = "armv6"
    else:
        goarch = "x86_64"

    # Darwin has no i386/armv6 builds in this release.
    if goos == "Darwin" and goarch not in ("x86_64", "arm64"):
        goarch = "arm64" if machine in ("aarch64", "arm64") else "x86_64"

    # Windows armv6 exists; keep mapping. Prefer arm64 when reported as arm64.
    archive_ext = "zip" if goos == "Windows" else "tar.gz"
    name = f"lux_{LUX_VERSION}_{goos}_{goarch}.{archive_ext}"
    return name, f"{LUX_RELEASE_BASE}/{name}"


# Back-compat alias: previous code imported a single Linux URL constant.
LUX_ASSET = resolve_lux_asset("Linux", "x86_64")[1]


def _lux_ready(path: Path | None = None) -> bool:
    path = path or LUX_BIN
    if not path.is_file():
        return False
    if sys.platform == "win32":
        return True
    return os.access(path, os.X_OK)


def _extract_lux_archive(archive: Path, dest_dir: Path, binary_name: str) -> bool:
    dest = dest_dir / binary_name
    if archive.suffixes[-2:] == [".tar", ".gz"] or archive.name.endswith(".tar.gz") or archive.suffix == ".tgz":
        with tarfile.open(archive, "r:gz") as tf:
            member = next(
                (
                    m
                    for m in tf.getmembers()
                    if Path(m.name).name in (binary_name, "lux", "lux.exe") and m.isfile()
                ),
                None,
            )
            if member is None:
                return False
            member.name = binary_name
            tf.extract(member, path=str(dest_dir))
    elif archive.suffix.lower() == ".zip" or archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as zf:
            member_name = next(
                (
                    n
                    for n in zf.namelist()
                    if Path(n).name in (binary_name, "lux", "lux.exe") and not n.endswith("/")
                ),
                None,
            )
            if member_name is None:
                return False
            with zf.open(member_name) as src, open(dest, "wb") as out:
                out.write(src.read())
    else:
        return False
    if dest.is_file() and sys.platform != "win32":
        dest.chmod(0o755)
    return dest.is_file()


def ensure_lux() -> bool:
    """Download the platform-matching lux release into bin/ if missing."""
    global _ENSURED, LUX_BIN
    LUX_BIN = lux_bin_path()
    if _lux_ready(LUX_BIN):
        return True
    if _ENSURED:
        return _lux_ready(LUX_BIN)
    _ENSURED = True
    try:
        asset_name, asset_url = resolve_lux_asset()
        LUX_BIN.parent.mkdir(parents=True, exist_ok=True)
        binary_name = lux_bin_name()
        suffix = ".zip" if asset_name.endswith(".zip") else ".tgz"
        tmp = LUX_BIN.parent / f".lux{suffix}"
        with httpx.Client(follow_redirects=True, timeout=60.0) as client:
            resp = client.get(asset_url)
            resp.raise_for_status()
            tmp.write_bytes(resp.content)
        ok = _extract_lux_archive(tmp, LUX_BIN.parent, binary_name)
        tmp.unlink(missing_ok=True)
        return ok and _lux_ready(LUX_BIN)
    except Exception:
        return False


# Private alias kept for older call sites / start scripts.
_ensure_lux = ensure_lux


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
        return ensure_lux()

    def version(self) -> str:
        if not LUX_BIN.is_file():
            return "missing"
        try:
            proc = subprocess.run([str(LUX_BIN), "-v"], capture_output=True, text=True, timeout=5)
            line = (proc.stdout or proc.stderr or "").strip().splitlines()
            return (line[0] if line else LUX_VERSION)[:80]
        except Exception:
            return LUX_VERSION

    def matches(self, url: str) -> bool:
        return is_douyin(url) or is_kuaishou(url)

    def extract(self, url: str) -> dict:
        if not ensure_lux():
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


if __name__ == "__main__":
    name, url = resolve_lux_asset()
    print(f"asset={name}")
    print(f"url={url}")
    print(f"bin={lux_bin_path()}")
    ok = ensure_lux()
    print(f"ensure_lux={ok}")
