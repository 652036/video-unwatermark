# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) where tagged.

## [Unreleased]

### Added

- Cross-platform lux bootstrap: auto-selects v0.24.1 release assets for Linux / macOS (Darwin) / Windows (x86_64 & arm64); Windows uses `lux.exe` + zip extract
- `start.ps1` / `start.bat` for Windows (venv, optional engines, Playwright Chromium tip, ffmpeg winget/choco tip, lux ensure)
- `start.sh` macOS support: Homebrew ffmpeg install attempt; Chrome.app detection; lux via `app.engines.lux.ensure_lux` (single source of truth)

### Documentation

- Quick Start sections for macOS / Linux / Windows; ffmpeg one-liners (brew / apt / winget); lux no longer documented as Linux amd64 only
- Locale READMEs (zh-CN + others) updated so Quick Start is not Linux-only

### Documentation (earlier)

- English landing README and multi-language docs (zh-CN, ja, ko, es, fr, de, pt-BR, ru, ar)
- Architecture notes, contributing / security policies, issue templates

## [1.1.0] - 2026-08

### Added

- Multi-engine public UGC parser (share-page, douyin-browser, yt-dlp, videofetch, you-get, webparser, lux)
- FastAPI UI + JSON API on port 8787
- Optional local Netscape / browser cookies as last resort
- Explicit VIP/DRM host block list
