"""Optional user-supplied cookies. Local file or local browser only."""

from __future__ import annotations

import logging
import os
import re
import tempfile
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path

from .config import BROWSER_CHOICES, COOKIE_UPLOAD_DIR, COOKIES_FILE, COOKIES_FROM_BROWSER

log = logging.getLogger("unwatermark")

_CTX: ContextVar[CookieOpts | None] = ContextVar("cookie_opts", default=None)

NETSCAPE_HINT = re.compile(r"(^# Netscape HTTP Cookie File)|(\t(TRUE|FALSE)\t)", re.I | re.M)
JSON_HINT = re.compile(r"^\s*[\[{]")


@dataclass(frozen=True)
class CookieOpts:
    cookiefile: str | None = None
    cookies_from_browser: str | None = None

    def configured(self) -> bool:
        return bool(self.cookiefile or self.cookies_from_browser)

    @classmethod
    def from_env(cls) -> CookieOpts:
        path = COOKIES_FILE
        if path and not Path(path).is_file():
            log.warning("UNWATERMARK_COOKIES path missing: %s", path)
            path = None
        browser = COOKIES_FROM_BROWSER
        if browser:
            err = validate_browser(browser)
            if err:
                log.warning("ignore COOKIES_FROM_BROWSER: %s", err)
                browser = None
        return cls(cookiefile=path, cookies_from_browser=browser)


def current() -> CookieOpts:
    return _CTX.get() or CookieOpts.from_env()


@contextmanager
def cookie_scope(opts: CookieOpts):
    token = _CTX.set(opts)
    try:
        yield
    finally:
        _CTX.reset(token)


def validate_browser(value: str) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    name = raw.split(":", 1)[0].strip().lower()
    if name not in BROWSER_CHOICES:
        return f"不支持的浏览器：{name}（可选：{', '.join(BROWSER_CHOICES)}）"
    return None


def validate_netscape(text: str) -> str | None:
    sample = (text or "").lstrip("\ufeff")
    if not sample.strip():
        return "cookies 文件为空"
    if JSON_HINT.match(sample):
        return "需要 Netscape 格式，不要上传 JSON。可用浏览器扩展「Get cookies.txt LOCALLY」导出"
    if NETSCAPE_HINT.search(sample):
        return None
    for line in sample.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 7:
            return None
    return "不是 Netscape cookies.txt（需要 # Netscape HTTP Cookie File 或制表符字段）"


def save_uploaded_cookies(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace")
    err = validate_netscape(text)
    if err:
        raise ValueError(err)
    if len(data) > 2 * 1024 * 1024:
        raise ValueError("cookies 文件过大")
    COOKIE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="c_", suffix=".txt", dir=str(COOKIE_UPLOAD_DIR))
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    path = Path(name)
    path.chmod(0o600)
    return str(path)


def resolve_local_path(path: str | None) -> str | None:
    if not path:
        return None
    p = Path(path).expanduser()
    if not p.is_file():
        raise ValueError("本机 cookies 路径不存在")
    text = p.read_text(encoding="utf-8", errors="replace")
    err = validate_netscape(text)
    if err:
        raise ValueError(err)
    return str(p.resolve())


def ytdlp_cookie_opts(opts: CookieOpts | None = None) -> dict:
    opts = opts or current()
    out: dict = {}
    if opts.cookiefile:
        out["cookiefile"] = opts.cookiefile
    if opts.cookies_from_browser:
        parts = [p if p else None for p in opts.cookies_from_browser.split(":")]
        out["cookiesfrombrowser"] = tuple(parts)
    return out


def httpx_cookie_dict(opts: CookieOpts | None = None) -> dict[str, str]:
    """Name->value from a Netscape file only. Browser extract is yt-dlp-only."""
    opts = opts or current()
    if not opts.cookiefile:
        return {}
    out: dict[str, str] = {}
    try:
        text = Path(opts.cookiefile).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    for raw in text.splitlines():
        line = raw[len("#HttpOnly_") :] if raw.startswith("#HttpOnly_") else raw
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        name, value = parts[5], parts[6]
        if name:
            out[name] = value
    return out
