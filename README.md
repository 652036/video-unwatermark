# video-unwatermark

Paste a **public** video share text or URL. The server races several extractors in parallel and returns a direct link (preferably without platform watermark) so you can download the original file.

<p align="center">
  <a href="README.md">EN</a> ·
  <a href="docs/zh-CN/README.md">zh-CN</a> ·
  <a href="docs/ja/README.md">ja</a> ·
  <a href="docs/ko/README.md">ko</a> ·
  <a href="docs/es/README.md">es</a> ·
  <a href="docs/fr/README.md">fr</a> ·
  <a href="docs/de/README.md">de</a> ·
  <a href="docs/pt-BR/README.md">pt-BR</a> ·
  <a href="docs/ru/README.md">ru</a> ·
  <a href="docs/ar/README.md">ar</a>
</p>

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688.svg)](https://fastapi.tiangolo.com/)

**Public UGC only.** Membership / DRM platforms (Tencent Video, iQIYI, Youku, Mango TV, Netflix, Disney+, HBO, Prime Video, Spotify, Hulu, and similar) are refused before any extractor runs. This project does not steal logins, phish cookies, or MITM WeChat Channels.

## Features

- Web UI at `http://127.0.0.1:8787` — paste share text or a URL, preview, download
- Multi-engine race: first successful extractor wins; others are cancelled
- Engines: `share-page`, `douyin-browser` (headless Chrome), `yt-dlp`, `videofetch`, `you-get`, `webparser`, `lux`
- Extracts the first `http(s)` URL from clipboard-style share slogans
- Optional local Netscape cookies / `--cookies-from-browser` as a **last resort** (never fetched for you)
- Explicit block list for VIP / DRM hosts; WeChat Channels login/MITM capture refused
- JSON API: parse, download, health, engines, OpenAPI at `/api/docs`

## Quick Start

### macOS / Linux

```bash
cd video-unwatermark
chmod +x start.sh
./start.sh
```

### Windows

```powershell
cd video-unwatermark
.\start.ps1
# or: start.bat
```

Open **http://127.0.0.1:8787**.

Manual install (any OS):

```bash
python3 -m venv .venv
# Windows: py -3 -m venv .venv && .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
# optional: pip install videofetch you-get
python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
```

`ffmpeg` should be on `PATH` (yt-dlp uses it to merge audio/video):

```bash
# macOS
brew install ffmpeg

# Debian / Ubuntu
sudo apt-get install ffmpeg

# Windows (pick one; may need admin)
winget install --id Gyan.FFmpeg -e
# choco install ffmpeg
```

`start.sh` / `start.ps1` also try to install optional engines (`videofetch`, `you-get`, Playwright) and auto-download the matching `lux` v0.24.1 release (Linux / macOS / Windows, x86_64 or arm64) into `bin/` when missing.

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/parse` | Body `{"url":"..."}` or multipart (`url`, optional `cookies_file`, `cookies_from_browser`) |
| `GET` | `/api/download?job=...` | Attachment download for a parse job |
| `GET` | `/api/preview?job=...` | Stream preview for a job |
| `GET` | `/api/health` | Engine + ffmpeg status; cookie flags only say *configured*, never contents |
| `GET` | `/api/engines` | Engine list |
| `GET` | `/api/docs` | OpenAPI UI |

Success payload includes `ok`, `title`, `ext`, `filesize`, `thumbnail`, `extractor`, `platform`, `download_url`, `direct_url`, `preview_url`, `job`. Guest blocks may return `{ok:false, needs_cookie:true, hint:"..."}`.

Timeouts: ~25s per engine, ~30s overall; Douyin/Kuaishou first race share-page + webparser + lux + `douyin-browser` (~25s), overall up to ~95s.

## Supported platforms & limits

| Engine | Typical sites | Notes |
|---|---|---|
| **share-page** | Douyin, Kuaishou | Guest share-page HTML (`_ROUTER_DATA` / `__APOLLO_STATE__`); no login cookie |
| **douyin-browser** | Douyin | Headless Chrome; captures CDN `video_mp4` from `iesdouyin.com/share/video/{id}/` |
| **yt-dlp** | YouTube, Bilibili, TikTok, Instagram, X, Facebook, Reddit, Weibo, Vimeo, … | Follow [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) |
| **videofetch** | Douyin, Kuaishou, Xiaohongshu, Bilibili, … | Public-UGC clients only; VIP movie clients disabled |
| **you-get** | Some CN / social sites | Extra fallback parser |
| **webparser** | Douyin, Kuaishou | Keyless public JSON helpers (e.g. 17change, douyin.wtf hybrid) |
| **lux** | Douyin, Kuaishou | Local `bin/lux` binary; fallback only |

Platform APIs change often; parse failures are normal. Login-walled content may return `needs_cookie`.

**Known limitations (honest):**

- **Douyin**: datacenter IPs often lack `play_addr` on share pages; yt-dlp may report `needs cookie`. Public hybrid parsers or `douyin-browser` may still succeed. Cookies are never stolen.
- **Kuaishou**: yt-dlp has no Kuaishou extractor. Existing `www.kuaishou.com/short-video/{id}` pages may parse via webparser; `v.kuaishou.com` shorts often expire; TLS EOF from some hosts is common.
- **Vimeo**: anonymous macos OAuth currently returns 401; use local `--cookies-from-browser` if you are logged in.
- **YouTube**: some IPs hit a bot wall (`Sign in to confirm you’re not a bot`); same optional local cookies apply.

## Optional cookies (last resort)

Some sites (especially Douyin / YouTube bot walls) block anonymous datacenter access. This tool **will not** obtain cookies for you. Do **not** paste cookies into chat.

On **your own machine**, provide **your own** Netscape cookies:

1. **CLI** (same idea as yt-dlp `--cookies` / `--cookies-from-browser`):

   ```bash
   # macOS / Linux
   ./start.sh --cookies /path/to/cookies.txt
   ./start.sh --cookies-from-browser chrome

   # Windows PowerShell
   .\start.ps1 -Cookies C:\path\to\cookies.txt
   .\start.ps1 -CookiesFromBrowser chrome
   ```

   `cookies_from_browser` only reads browsers installed on **that** machine. Useless on a remote VPS without your profile.

2. **Environment**

   ```bash
   export UNWATERMARK_COOKIES=/path/to/cookies.txt
   export UNWATERMARK_COOKIES_FROM_BROWSER=chrome   # optional, local only
   ./start.sh
   ```

3. **Web / API** — expand “Local Cookies” on the page, upload Netscape `cookies.txt` (e.g. via [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)), or set `cookies_from_browser`. JSON cookie exports are rejected.

Uploaded files are used only for that parse/download; they are not traded to third-party ticket APIs.

## Architecture

FastAPI serves `static/` and JSON routes. `app/extract.py` expands short links, rejects blocked hosts, then runs staged engine races (`share-page` / `douyin-browser` / core / fallback). The first `ok` result creates a short-lived job; `/api/download` materializes the file (with ffmpeg merge when needed). Details: [docs/architecture.md](docs/architecture.md). Docs index: [docs/README.md](docs/README.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security reports: [SECURITY.md](SECURITY.md). Changes: [CHANGELOG.md](CHANGELOG.md).

## License

[Apache License 2.0](LICENSE) — Copyright 2026 652036. Third-party engines remain under their own licenses; see [NOTICE](NOTICE).

## Disclaimer

Download only public content you have the right to save. Respect each platform’s terms and local law. This project does **not** provide membership cracking, DRM decryption, or unauthorized access.
