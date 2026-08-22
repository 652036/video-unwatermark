"""Extractor engines. Each exposes name/available/version/extract(url)."""

from __future__ import annotations

from typing import Protocol


class Engine(Protocol):
    name: str

    def available(self) -> bool: ...
    def version(self) -> str: ...
    def extract(self, url: str) -> dict: ...


def load_engines() -> list:
    engines = []
    try:
        from .douyin_browser import DouyinBrowserEngine

        engines.append(DouyinBrowserEngine())
    except Exception:
        pass
    try:
        from .sharepage import SharePageEngine

        engines.append(SharePageEngine())
    except Exception:
        pass
    from .ytdlp import YtDlpEngine

    engines.append(YtDlpEngine())
    try:
        from .videofetch_engine import VideofetchEngine

        engines.append(VideofetchEngine())
    except Exception:
        pass
    try:
        from .youget import YouGetEngine

        engines.append(YouGetEngine())
    except Exception:
        pass
    try:
        from .webparser import WebParserEngine

        engines.append(WebParserEngine())
    except Exception:
        pass
    try:
        from .lux import LuxEngine

        engines.append(LuxEngine())
    except Exception:
        pass
    return engines
