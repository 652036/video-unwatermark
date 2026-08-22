# video-unwatermark

Pega un texto o URL de vídeo **público**. El servidor hace competir varios extractores en paralelo y devuelve un enlace directo (preferiblemente sin marca de agua) para descargar el archivo original.

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

**Solo UGC público.** Las plataformas con membresía / DRM (Tencent Video, iQIYI, Youku, Mango TV, Netflix, Disney+, HBO, Prime Video, Spotify, Hulu y similares) se rechazan antes de ejecutar extractores. Este proyecto no roba inicios de sesión, no pesca cookies ni hace MITM de WeChat Channels.

## Características

- UI web en `http://127.0.0.1:8787` — pegar texto/URL, previsualizar, descargar
- Carrera multi-motor: gana el primero que tenga éxito; el resto se cancela
- Motores: `share-page`, `douyin-browser` (Chrome headless), `yt-dlp`, `videofetch`, `you-get`, `webparser`, `lux`
- Extrae la primera URL `http(s)` de eslóganes de compartir
- Cookies Netscape locales / `--cookies-from-browser` opcionales como **último recurso** (nunca se obtienen por ti)
- Lista explícita de bloqueo VIP / DRM; rechazo de captura tipo login/MITM de WeChat Channels
- API JSON: parse, download, health, engines; OpenAPI en `/api/docs`

## Inicio rápido

```bash
cd video-unwatermark
chmod +x start.sh
./start.sh
```

Abre **http://127.0.0.1:8787**.

Instalación manual:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# optional: pip install videofetch you-get
python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
```

`ffmpeg` debe estar en el `PATH` (yt-dlp fusiona audio/vídeo). En Debian/Ubuntu:

```bash
sudo apt-get install ffmpeg
```

`start.sh` también intenta instalar motores opcionales (`videofetch`, `you-get`, Playwright) y descarga `lux` Linux amd64 en `bin/` si falta.

## Captura de pantalla

![Web UI](../images/ui.png)

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/parse` | Body `{"url":"..."}` or multipart (`url`, optional `cookies_file`, `cookies_from_browser`) |
| `GET` | `/api/download?job=...` | Attachment download for a parse job |
| `GET` | `/api/preview?job=...` | Stream preview for a job |
| `GET` | `/api/health` | Engine + ffmpeg status; cookie flags only say *configured*, never contents |
| `GET` | `/api/engines` | Engine list |
| `GET` | `/api/docs` | OpenAPI UI |

La respuesta correcta incluye `ok`, `title`, `ext`, `filesize`, `thumbnail`, `extractor`, `platform`, `download_url`, `direct_url`, `preview_url`, `job`. Si el acceso de invitado está bloqueado puede devolver `{ok:false, needs_cookie:true, hint:"..."}`.

Tiempos de espera: ~25 s por motor, ~30 s en total; Douyin/Kuaishou primero compiten share-page + webparser + lux + `douyin-browser` (~25 s), hasta ~95 s en total.

## Sitios admitidos y límites

| Engine | Typical sites | Notes |
|---|---|---|
| **share-page** | Douyin, Kuaishou | Guest share-page HTML (`_ROUTER_DATA` / `__APOLLO_STATE__`); no login cookie |
| **douyin-browser** | Douyin | Headless Chrome; captures CDN `video_mp4` from `iesdouyin.com/share/video/{id}/` |
| **yt-dlp** | YouTube, Bilibili, TikTok, Instagram, X, Facebook, Reddit, Weibo, Vimeo, … | Follow [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) |
| **videofetch** | Douyin, Kuaishou, Xiaohongshu, Bilibili, … | Public-UGC clients only; VIP movie clients disabled |
| **you-get** | Some CN / social sites | Extra fallback parser |
| **webparser** | Douyin, Kuaishou | Keyless public JSON helpers (e.g. 17change, douyin.wtf hybrid) |
| **lux** | Douyin, Kuaishou | Local `bin/lux` binary; fallback only |

Las APIs de las plataformas cambian a menudo; los fallos son normales. El contenido tras muro de login puede devolver `needs_cookie`.

**Limitaciones conocidas (con honestidad):**

- **Douyin**: datacenter IPs often lack `play_addr` on share pages; yt-dlp may report `needs cookie`. Public hybrid parsers or `douyin-browser` may still succeed. Cookies are never stolen.
- **Kuaishou**: yt-dlp has no Kuaishou extractor. Existing `www.kuaishou.com/short-video/{id}` pages may parse via webparser; `v.kuaishou.com` shorts often expire; TLS EOF from some hosts is common.
- **Vimeo**: anonymous macos OAuth currently returns 401; use local `--cookies-from-browser` if you are logged in.
- **YouTube**: some IPs hit a bot wall (`Sign in to confirm you’re not a bot`); same optional local cookies apply.

Notas de prueba: [../test-results.md](../test-results.md)

## Cookies opcionales (último recurso)

Algunos sitios (sobre todo Douyin / muro de bots de YouTube) bloquean IPs de centro de datos. Esta herramienta **no** obtiene cookies por ti. **No** pegues cookies en el chat.

En **tu propia máquina**, aporta **tus** cookies Netscape:

1. **CLI**

```bash
./start.sh --cookies /path/to/cookies.txt
./start.sh --cookies-from-browser chrome
```

   `cookies_from_browser` solo lee navegadores instalados en **esa** máquina. En un VPS remoto sin tu perfil no sirve.

2. **Variables de entorno**

```bash
export UNWATERMARK_COOKIES=/path/to/cookies.txt
export UNWATERMARK_COOKIES_FROM_BROWSER=chrome   # optional, local only
./start.sh
```

3. **Web / API** — expande «Local Cookies», sube Netscape `cookies.txt` o elige `cookies_from_browser`. Se rechazan exportaciones JSON.

Los archivos subidos solo se usan en ese parse/download; no se cambian por tickets de terceros.

## Arquitectura

FastAPI sirve `static/` y rutas JSON. `app/extract.py` expande enlaces cortos, rechaza hosts bloqueados y ejecuta carreras por etapas. El primer `ok` crea un job breve; `/api/download` materializa el archivo (con fusión ffmpeg si hace falta). Detalles: [../architecture.md](../architecture.md). Índice: [../README.md](../README.md).

## Contribuir

Ver [../../CONTRIBUTING.md](../../CONTRIBUTING.md). Seguridad: [../../SECURITY.md](../../SECURITY.md). Cambios: [../../CHANGELOG.md](../../CHANGELOG.md).

## Licencia

[Apache License 2.0](../../LICENSE) — Copyright 2026 652036. Los motores de terceros conservan sus licencias; ver [../../NOTICE](../../NOTICE).

## Aviso legal

Descarga solo contenido público que tengas derecho a guardar. Respeta los términos de cada plataforma y la ley local. Este proyecto **no** ofrece crack de membresías, descifrado DRM ni acceso no autorizado.
