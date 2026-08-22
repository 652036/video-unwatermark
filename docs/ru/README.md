# video-unwatermark

Вставьте **публичный** текст шаринга или URL видео. Сервер параллельно запускает несколько экстракторов и возвращает прямую ссылку (по возможности без водяного знака) для скачивания исходного файла.

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

**Только публичный UGC.** Платформы с подпиской / DRM (Tencent Video, iQIYI, Youku, Mango TV, Netflix, Disney+, HBO, Prime Video, Spotify, Hulu и аналоги) отклоняются до запуска экстракторов. Проект не крадёт логины, не фишит cookies и не делает MITM WeChat Channels.

## Возможности

- Веб-интерфейс на `http://127.0.0.1:8787` — вставка текста/URL, превью, скачивание
- Гонка движков: побеждает первый успех; остальные отменяются
- Движки: `share-page`, `douyin-browser` (headless Chrome), `yt-dlp`, `videofetch`, `you-get`, `webparser`, `lux`
- Извлекает первый `http(s)` URL из слоганов шаринга
- Опциональные локальные Netscape cookies / `--cookies-from-browser` как **крайняя мера** (никогда не добываются за вас)
- Явный блок-лист VIP / DRM; отказ от login/MITM WeChat Channels
- JSON API: parse, download, health, engines; OpenAPI на `/api/docs`

## Быстрый старт

```bash
cd video-unwatermark
chmod +x start.sh
./start.sh
```

Откройте **http://127.0.0.1:8787**.

Ручная установка:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# optional: pip install videofetch you-get
python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
```

`ffmpeg` должен быть в `PATH` (слияние аудио/видео yt-dlp). Debian/Ubuntu:

```bash
sudo apt-get install ffmpeg
```

`start.sh` также пытается поставить опциональные движки (`videofetch`, `you-get`, Playwright) и скачивает `lux` Linux amd64 в `bin/` при отсутствии.

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/parse` | Body `{"url":"..."}` or multipart (`url`, optional `cookies_file`, `cookies_from_browser`) |
| `GET` | `/api/download?job=...` | Attachment download for a parse job |
| `GET` | `/api/preview?job=...` | Stream preview for a job |
| `GET` | `/api/health` | Engine + ffmpeg status; cookie flags only say *configured*, never contents |
| `GET` | `/api/engines` | Engine list |
| `GET` | `/api/docs` | OpenAPI UI |

Успешный ответ включает `ok`, `title`, `ext`, `filesize`, `thumbnail`, `extractor`, `platform`, `download_url`, `direct_url`, `preview_url`, `job`. При блокировке гостя возможно `{ok:false, needs_cookie:true, hint:"..."}`.

Таймауты: ~25 с на движок, ~30 с всего; для Douyin/Kuaishou сначала гоняются share-page + webparser + lux + `douyin-browser` (~25 с), всего до ~95 с.

## Поддерживаемые сайты и ограничения

| Engine | Typical sites | Notes |
|---|---|---|
| **share-page** | Douyin, Kuaishou | Guest share-page HTML (`_ROUTER_DATA` / `__APOLLO_STATE__`); no login cookie |
| **douyin-browser** | Douyin | Headless Chrome; captures CDN `video_mp4` from `iesdouyin.com/share/video/{id}/` |
| **yt-dlp** | YouTube, Bilibili, TikTok, Instagram, X, Facebook, Reddit, Weibo, Vimeo, … | Follow [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) |
| **videofetch** | Douyin, Kuaishou, Xiaohongshu, Bilibili, … | Public-UGC clients only; VIP movie clients disabled |
| **you-get** | Some CN / social sites | Extra fallback parser |
| **webparser** | Douyin, Kuaishou | Keyless public JSON helpers (e.g. 17change, douyin.wtf hybrid) |
| **lux** | Douyin, Kuaishou | Local `bin/lux` binary; fallback only |

API площадок часто меняются; сбои — норма. Контент за логином может вернуть `needs_cookie`.

**Известные ограничения (честно):**

- **Douyin**: datacenter IPs often lack `play_addr` on share pages; yt-dlp may report `needs cookie`. Public hybrid parsers or `douyin-browser` may still succeed. Cookies are never stolen.
- **Kuaishou**: yt-dlp has no Kuaishou extractor. Existing `www.kuaishou.com/short-video/{id}` pages may parse via webparser; `v.kuaishou.com` shorts often expire; TLS EOF from some hosts is common.
- **Vimeo**: anonymous macos OAuth currently returns 401; use local `--cookies-from-browser` if you are logged in.
- **YouTube**: some IPs hit a bot wall (`Sign in to confirm you’re not a bot`); same optional local cookies apply.

## Опциональные cookies (крайняя мера)

Некоторые сайты (особенно Douyin / bot wall YouTube) режут анонимный доступ с датацентровых IP. Инструмент **не** получает cookies за вас. **Не** вставляйте cookies в чат.

На **своей машине** передайте **свои** Netscape cookies:

1. **CLI**

```bash
./start.sh --cookies /path/to/cookies.txt
./start.sh --cookies-from-browser chrome
```

   `cookies_from_browser` читает только браузеры на **этой** машине. На удалённом VPS без вашего профиля бесполезно.

2. **Переменные окружения**

```bash
export UNWATERMARK_COOKIES=/path/to/cookies.txt
export UNWATERMARK_COOKIES_FROM_BROWSER=chrome   # optional, local only
./start.sh
```

3. **Web / API** — раскройте «Local Cookies», загрузите Netscape `cookies.txt` или выберите `cookies_from_browser`. JSON-экспорты отклоняются.

Загруженные файлы используются только в данном parse/download; их не обменивают на сторонние тикеты.

## Архитектура

FastAPI отдаёт `static/` и JSON. `app/extract.py` раскрывает короткие ссылки, отклоняет запрещённые хосты и запускает поэтапные гонки. Первый `ok` создаёт короткий job; `/api/download` материализует файл (при необходимости merge через ffmpeg). Подробнее: [../architecture.md](../architecture.md). Оглавление: [../README.md](../README.md).

## Участие

См. [../../CONTRIBUTING.md](../../CONTRIBUTING.md). Безопасность: [../../SECURITY.md](../../SECURITY.md). Изменения: [../../CHANGELOG.md](../../CHANGELOG.md).

## Лицензия

[Apache License 2.0](../../LICENSE) — Copyright 2026 652036. Сторонние движки остаются под своими лицензиями; см. [../../NOTICE](../../NOTICE).

## Отказ от ответственности

Скачивайте только публичный контент, который вы вправе сохранять. Соблюдайте правила площадок и местное право. Проект **не** предоставляет взлом подписок, расшифровку DRM или несанкционированный доступ.
