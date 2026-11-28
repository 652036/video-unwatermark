# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) where tagged.

## [1.2.1]

### Fixed

- **Douyin download speed (5x–6x faster)**: added dedicated HTTP/1.1 multi-socket download client (`downloadH1`) to bypass per-TCP-connection CDN throttling caused by HTTP/2 multiplexing, reused the resolved 302 CDN URL once during probe (`Range: bytes=0-1`), and switched to an adaptive work-stealing segment queue (4–8 workers for files ≥ 512 KB).
- **Douyin first-try auto extraction**: added `douyinvod.com`, `zjcdn.com`, and `/video/tos/` CDN recognition, hydrated `window._ROUTER_DATA` capture, muted `<video>` play nudge, `performance.getEntriesByType('resource')` scanning, and real mobile viewport layout in background `WebViewSniffer` so Douyin no longer requires opening the interactive browser.

## [1.2.0]

### Added

- Android multi-threaded HTTP Range parallel downloader (3–6 concurrent threads via `FileChannel` + 256 KB buffered `MediaStore` writes) with live download speed (`MB/s`) display.
- Android Foreground Service (`DownloadService`, `dataSync`) for background/screen-off downloads with live notification progress bar, Cancel action, and tap-to-play completion notification.
- On-demand ExoPlayer preview (shows cover thumbnail first and releases player before download to avoid CDN bandwidth/connection contention).

### Fixed

- Instant socket cancellation (`Call.cancel()`) and guaranteed cleanup of partial `.tmp` cache files and incomplete `MediaStore` entries when cancelling or clearing an active download.

## [1.1.0]

### Added

- Standalone Android APK (`android/`, Kotlin + Jetpack Compose + OkHttp + Media3 ExoPlayer + WebView sniffer) running fully on-device without a backend server (~2.2 MB Release APK).
- On-device native extractors for Douyin, Kuaishou, Xianyu (`m.tb.cn` + H5/PC MTOP), Xiaohongshu, Bilibili, YouTube, TikTok, X (Twitter), Instagram, Facebook, Reddit, Vimeo, and generic HTML/direct media.
- System Share menu (`ACTION_SEND`) integration, in-app ExoPlayer preview, MediaStore gallery download (`Movies/VideoExtractor`), and interactive local WebView login/sniffer dialog.
- Android JUnit test suite (16 tests) and GitHub Actions workflow (`.github/workflows/android.yml`) building and publishing `video-extractor-android.apk`.

## [1.0.0]

### Added

- Multi-engine public UGC video extractor (`share-page`, `douyin-browser`, `xianyu`, `yt-dlp`, `videofetch`, `you-get`, `webparser`, `lux`) with FastAPI Web UI and JSON API on port 8787.
- Xianyu (闲鱼 / `goofish.com` / `2.taobao.com` / `m.tb.cn`) extractor supporting `m.tb.cn` JS redirect expansion, H5 guest MTOP API (`mtop.taobao.idle.awesome.detail`), PC MTOP + UD/HD video query (`mtop.idle.cloud.video.query`) with scoped local cookies, and headless Chrome passive capture fallback.
- Share URL integrity handling: preserves percent-encoded paths and signed query parameters, enforces strict domain-label host boundaries, and normalizes trailing DNS root dots.
- Optional local Netscape `cookies.txt` and `--cookies-from-browser` support (`VIDEO_EXTRACTOR_COOKIES` / `VIDEO_EXTRACTOR_COOKIES_FROM_BROWSER`).
- Explicit VIP / DRM host block list and refusal of WeChat Channels login/MITM capture.
- Cross-platform startup scripts (`start.sh`, `start.ps1`, `start.bat`) with automatic `lux` binary bootstrap.
- Offline unit, URL integrity, and FastAPI endpoint test suites (`tests/test_core.py`, `tests/test_url_integrity.py`, `tests/test_xianyu.py`) executed in CI.
