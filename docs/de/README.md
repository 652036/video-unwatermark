# video-unwatermark

Fügen Sie einen **öffentlichen** Video-Share-Text oder eine URL ein. Der Server lässt mehrere Extraktoren parallel gegeneinander laufen und liefert einen Direktlink (möglichst ohne Wasserzeichen) zum Download der Originaldatei.

<p align="center">
  <a href="../../README.md">EN</a> ·
  <a href="../zh-CN/README.md">zh-CN</a> ·
  <a href="../ja/README.md">ja</a> ·
  <a href="../ko/README.md">ko</a> ·
  <a href="../es/README.md">es</a> ·
  <a href="../fr/README.md">fr</a> ·
  <a href="../de/README.md">de</a> ·
  <a href="../pt-BR/README.md">pt-BR</a> ·
  <a href="../ru/README.md">ru</a> ·
  <a href="../ar/README.md">ar</a>
</p>

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](../../LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688.svg)](https://fastapi.tiangolo.com/)

**Nur öffentliches UGC.** Abo-/DRM-Plattformen (Tencent Video, iQIYI, Youku, Mango TV, Netflix, Disney+, HBO, Prime Video, Spotify, Hulu u. a.) werden vor jedem Extraktor abgelehnt. Kein Login-Diebstahl, kein Cookie-Phishing, kein WeChat-Channels-MITM.

## Funktionen

- Web-UI unter `http://127.0.0.1:8787` — Text/URL einfügen, Vorschau, Download
- Multi-Engine-Race: der erste Erfolg gewinnt; andere werden abgebrochen
- Engines: `share-page`, `douyin-browser` (Headless Chrome), `yt-dlp`, `videofetch`, `you-get`, `webparser`, `lux`
- Extrahiert die erste `http(s)`-URL aus Share-Slogans
- Optionale lokale Netscape-Cookies / `--cookies-from-browser` als **letzte Option** (werden nie für Sie geholt)
- Explizite VIP-/DRM-Sperrliste; Ablehnung von WeChat-Channels-Login/MITM
- JSON-API: parse, download, health, engines; OpenAPI unter `/api/docs`

## Schnellstart

```bash
cd video-unwatermark
chmod +x start.sh
./start.sh
```

Windows: `.\start.ps1` (oder `start.bat`).

Öffnen Sie **http://127.0.0.1:8787**.

Manuelle Installation:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# optional: pip install videofetch you-get
python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
```

`ffmpeg` sollte im `PATH` liegen (yt-dlp Audio/Video-Merge):

```bash
# macOS
brew install ffmpeg
# Debian / Ubuntu
sudo apt-get install ffmpeg
# Windows
winget install --id Gyan.FFmpeg -e
```

`start.sh` (macOS/Linux) oder `start.ps1` (Windows) versucht optionale Engines (`videofetch`, `you-get`, Playwright) zu installieren und lädt bei Bedarf das passende `lux` für Ihr OS/CPU nach `bin/`.

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/parse` | Body `{"url":"..."}` or multipart (`url`, optional `cookies_file`, `cookies_from_browser`) |
| `GET` | `/api/download?job=...` | Attachment download for a parse job |
| `GET` | `/api/preview?job=...` | Stream preview for a job |
| `GET` | `/api/health` | Engine + ffmpeg status; cookie flags only say *configured*, never contents |
| `GET` | `/api/engines` | Engine list |
| `GET` | `/api/docs` | OpenAPI UI |

Erfolgreiche Antworten enthalten `ok`, `title`, `ext`, `filesize`, `thumbnail`, `extractor`, `platform`, `download_url`, `direct_url`, `preview_url`, `job`. Gast-Sperren können `{ok:false, needs_cookie:true, hint:"..."}` liefern.

Timeouts: ~25 s pro Engine, ~30 s insgesamt; Douyin/Kuaishou starten zuerst share-page + webparser + lux + `douyin-browser` (~25 s), insgesamt bis ~95 s.

## Unterstützte Seiten & Grenzen

| Engine | Typical sites | Notes |
|---|---|---|
| **share-page** | Douyin, Kuaishou | Guest share-page HTML (`_ROUTER_DATA` / `__APOLLO_STATE__`); no login cookie |
| **douyin-browser** | Douyin | Headless Chrome; captures CDN `video_mp4` from `iesdouyin.com/share/video/{id}/` |
| **yt-dlp** | YouTube, Bilibili, TikTok, Instagram, X, Facebook, Reddit, Weibo, Vimeo, … | Follow [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) |
| **videofetch** | Douyin, Kuaishou, Xiaohongshu, Bilibili, … | Public-UGC clients only; VIP movie clients disabled |
| **you-get** | Some CN / social sites | Extra fallback parser |
| **webparser** | Douyin, Kuaishou | Keyless public JSON helpers (e.g. 17change, douyin.wtf hybrid) |
| **lux** | Douyin, Kuaishou | Local `bin/lux` binary; fallback only |

Plattform-APIs ändern sich oft; Fehlschläge sind normal. Login-geschützte Inhalte können `needs_cookie` zurückgeben.

**Bekannte Grenzen (ehrlich):**

- **Douyin**: datacenter IPs often lack `play_addr` on share pages; yt-dlp may report `needs cookie`. Public hybrid parsers or `douyin-browser` may still succeed. Cookies are never stolen.
- **Kuaishou**: yt-dlp has no Kuaishou extractor. Existing `www.kuaishou.com/short-video/{id}` pages may parse via webparser; `v.kuaishou.com` shorts often expire; TLS EOF from some hosts is common.
- **Vimeo**: anonymous macos OAuth currently returns 401; use local `--cookies-from-browser` if you are logged in.
- **YouTube**: some IPs hit a bot wall (`Sign in to confirm you’re not a bot`); same optional local cookies apply.

## Optionale Cookies (letzte Option)

Manche Seiten (besonders Douyin / YouTube-Bot-Wall) blockieren Rechenzentrums-IPs. Dieses Tool **holt keine** Cookies für Sie. Cookies **nicht** in Chats einfügen.

Auf **Ihrem Rechner** nur **Ihre** Netscape-Cookies angeben:

1. **CLI**

```bash
./start.sh --cookies /path/to/cookies.txt
./start.sh --cookies-from-browser chrome
```

   `cookies_from_browser` liest nur Browser auf **diesem** Rechner. Auf einem Remote-VPS ohne Ihr Profil wirkungslos.

2. **Umgebungsvariablen**

```bash
export UNWATERMARK_COOKIES=/path/to/cookies.txt
export UNWATERMARK_COOKIES_FROM_BROWSER=chrome   # optional, local only
./start.sh
```

3. **Web / API** — „Local Cookies“ öffnen, Netscape `cookies.txt` hochladen oder `cookies_from_browser` wählen. JSON-Cookie-Exporte werden abgelehnt.

Hochgeladene Dateien gelten nur für diesen Parse/Download; sie werden nicht gegen Drittanbieter-Tickets getauscht.

## Architektur

FastAPI liefert `static/` und JSON-Routen. `app/extract.py` expandiert Kurzlinks, lehnt gesperrte Hosts ab und führt gestufte Engine-Races aus. Der erste `ok`-Treffer erzeugt einen kurzlebigen Job; `/api/download` materialisiert die Datei (ffmpeg-Merge bei Bedarf). Details: [../architecture.md](../architecture.md). Index: [../README.md](../README.md).

## Mitwirken

Siehe [../../CONTRIBUTING.md](../../CONTRIBUTING.md). Sicherheit: [../../SECURITY.md](../../SECURITY.md). Änderungen: [../../CHANGELOG.md](../../CHANGELOG.md).

## Lizenz

[Apache License 2.0](../../LICENSE) — Copyright 2026 652036. Drittanbieter-Engines behalten ihre Lizenzen; siehe [../../NOTICE](../../NOTICE).

## Haftungsausschluss

Laden Sie nur öffentliches Material herunter, das Sie speichern dürfen. Beachten Sie Plattformbedingungen und lokales Recht. Dieses Projekt bietet **keine** Abo-Cracks, DRM-Entschlüsselung oder unautorisierten Zugriff.
