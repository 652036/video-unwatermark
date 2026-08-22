# Architecture

`video-unwatermark` is a small FastAPI app that turns a public share text or URL into a downloadable media file.

## Request flow

1. **UI / API** — `static/` is served at `/`. `POST /api/parse` accepts JSON or multipart (optional Netscape cookies).
2. **Normalize** — `app/extract.py` / `app/urls.py` pull the first `http(s)` URL from share slogans, expand short links, and refuse VIP/DRM hosts (`app/config.py` `BLOCKED_HOSTS`) plus WeChat Channels MITM-style targets.
3. **Staged race** — Available engines from `app/engines/` run in stages. For Douyin/Kuaishou, `share-page`, `webparser`, `lux`, and `douyin-browser` race early so a yt-dlp `needs cookie` cannot consume the whole budget. Core engines (`yt-dlp`, `videofetch`, `you-get`) run next; fallbacks may run again. First `ok` wins; others are cancelled.
4. **Job** — Success creates a short-lived job in `app/jobs.py` with metadata and optional `direct_url`.
5. **Materialize** — `GET /api/download` / `/api/preview` call `app/download.py` (yt-dlp + ffmpeg merge when needed). Cookies stay scoped via `app/cookies.py` and are never fetched from websites for you.

## Engines (honest)

| Name | Role |
|---|---|
| `share-page` | Guest HTML parse for Douyin/Kuaishou share pages |
| `douyin-browser` | Headless Chrome network capture on `iesdouyin.com/share/video/{id}/` |
| `yt-dlp` | Broad site coverage |
| `videofetch` | Extra CN short-video clients (public UGC allow-list only) |
| `you-get` | Additional fallback |
| `webparser` | Keyless public JSON helpers |
| `lux` | Optional local `bin/lux` binary |

Timeouts live in `app/config.py` (`ENGINE_TIMEOUT`, `OVERALL_TIMEOUT`, `CN_OVERALL_TIMEOUT`, `BROWSER_TIMEOUT`).

## What this is not

No membership unlock, DRM decrypt, login theft, cookie phishing, or WeChat Channels middleman. Optional cookies are user-supplied Netscape files or local `--cookies-from-browser` only.
