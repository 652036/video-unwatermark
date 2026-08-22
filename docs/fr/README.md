# video-unwatermark

Collez un texte de partage ou une URL de vidéo **publique**. Le serveur fait concourir plusieurs extracteurs en parallèle et renvoie un lien direct (de préférence sans filigrane) pour télécharger le fichier d’origine.

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

**UGC public uniquement.** Les plateformes d’abonnement / DRM (Tencent Video, iQIYI, Youku, Mango TV, Netflix, Disney+, HBO, Prime Video, Spotify, Hulu, etc.) sont refusées avant tout extracteur. Ce projet ne vole pas de sessions, ne pêche pas de cookies et ne fait pas de MITM WeChat Channels.

## Fonctionnalités

- Interface web sur `http://127.0.0.1:8787` — coller texte/URL, prévisualiser, télécharger
- Course multi-moteurs : le premier succès gagne ; les autres sont annulés
- Moteurs : `share-page`, `douyin-browser` (Chrome headless), `yt-dlp`, `videofetch`, `you-get`, `webparser`, `lux`
- Extrait la première URL `http(s)` des slogans de partage
- Cookies Netscape locaux / `--cookies-from-browser` optionnels en **dernier recours** (jamais récupérés pour vous)
- Liste de blocage VIP / DRM explicite ; refus de capture login/MITM WeChat Channels
- API JSON : parse, download, health, engines ; OpenAPI sur `/api/docs`

## Démarrage rapide

```bash
cd video-unwatermark
chmod +x start.sh
./start.sh
```

Ouvrez **http://127.0.0.1:8787**.

Installation manuelle :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# optional: pip install videofetch you-get
python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
```

`ffmpeg` doit être dans le `PATH` (fusion audio/vidéo yt-dlp). Sur Debian/Ubuntu :

```bash
sudo apt-get install ffmpeg
```

`start.sh` tente aussi d’installer les moteurs optionnels (`videofetch`, `you-get`, Playwright) et télécharge `lux` Linux amd64 dans `bin/` si besoin.

## Capture d’écran

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

La réponse de succès inclut `ok`, `title`, `ext`, `filesize`, `thumbnail`, `extractor`, `platform`, `download_url`, `direct_url`, `preview_url`, `job`. Un accès invité bloqué peut renvoyer `{ok:false, needs_cookie:true, hint:"..."}`.

Délais : ~25 s par moteur, ~30 s au total ; Douyin/Kuaishou font d’abord courir share-page + webparser + lux + `douyin-browser` (~25 s), jusqu’à ~95 s au total.

## Sites pris en charge et limites

| Engine | Typical sites | Notes |
|---|---|---|
| **share-page** | Douyin, Kuaishou | Guest share-page HTML (`_ROUTER_DATA` / `__APOLLO_STATE__`); no login cookie |
| **douyin-browser** | Douyin | Headless Chrome; captures CDN `video_mp4` from `iesdouyin.com/share/video/{id}/` |
| **yt-dlp** | YouTube, Bilibili, TikTok, Instagram, X, Facebook, Reddit, Weibo, Vimeo, … | Follow [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) |
| **videofetch** | Douyin, Kuaishou, Xiaohongshu, Bilibili, … | Public-UGC clients only; VIP movie clients disabled |
| **you-get** | Some CN / social sites | Extra fallback parser |
| **webparser** | Douyin, Kuaishou | Keyless public JSON helpers (e.g. 17change, douyin.wtf hybrid) |
| **lux** | Douyin, Kuaishou | Local `bin/lux` binary; fallback only |

Les API des plateformes changent souvent ; les échecs sont normaux. Un contenu derrière un login peut renvoyer `needs_cookie`.

**Limites connues (honnêtes) :**

- **Douyin**: datacenter IPs often lack `play_addr` on share pages; yt-dlp may report `needs cookie`. Public hybrid parsers or `douyin-browser` may still succeed. Cookies are never stolen.
- **Kuaishou**: yt-dlp has no Kuaishou extractor. Existing `www.kuaishou.com/short-video/{id}` pages may parse via webparser; `v.kuaishou.com` shorts often expire; TLS EOF from some hosts is common.
- **Vimeo**: anonymous macos OAuth currently returns 401; use local `--cookies-from-browser` if you are logged in.
- **YouTube**: some IPs hit a bot wall (`Sign in to confirm you’re not a bot`); same optional local cookies apply.

Notes de test : [../test-results.md](../test-results.md)

## Cookies optionnels (dernier recours)

Certains sites (surtout Douyin / mur anti-bot YouTube) bloquent les IP de datacenter. Cet outil **n’obtient pas** de cookies pour vous. **Ne collez pas** de cookies dans un chat.

Sur **votre machine**, fournissez **vos** cookies Netscape :

1. **CLI**

```bash
./start.sh --cookies /path/to/cookies.txt
./start.sh --cookies-from-browser chrome
```

   `cookies_from_browser` ne lit que les navigateurs installés sur **cette** machine. Inutile sur un VPS distant sans votre profil.

2. **Variables d’environnement**

```bash
export UNWATERMARK_COOKIES=/path/to/cookies.txt
export UNWATERMARK_COOKIES_FROM_BROWSER=chrome   # optional, local only
./start.sh
```

3. **Web / API** — développez « Local Cookies », téléversez un Netscape `cookies.txt` ou choisissez `cookies_from_browser`. Les exports JSON sont refusés.

Les fichiers ne servent qu’au parse/download concerné ; ils ne sont pas échangés contre des tickets tiers.

## Architecture

FastAPI sert `static/` et les routes JSON. `app/extract.py` développe les liens courts, refuse les hôtes bloqués, puis lance des courses par étapes. Le premier `ok` crée un job court ; `/api/download` matérialise le fichier (fusion ffmpeg si besoin). Détails : [../architecture.md](../architecture.md). Index : [../README.md](../README.md).

## Contribution

Voir [../../CONTRIBUTING.md](../../CONTRIBUTING.md). Sécurité : [../../SECURITY.md](../../SECURITY.md). Journal : [../../CHANGELOG.md](../../CHANGELOG.md).

## Licence

[Apache License 2.0](../../LICENSE) — Copyright 2026 652036. Les moteurs tiers restent sous leurs licences ; voir [../../NOTICE](../../NOTICE).

## Avertissement

Ne téléchargez que du contenu public que vous avez le droit de conserver. Respectez les conditions des plateformes et le droit local. Ce projet **ne fournit pas** de crack d’abonnement, de déchiffrement DRM ni d’accès non autorisé.
