# video-unwatermark

**공개** 동영상 공유 문구 또는 URL을 붙여넣으면, 서버가 여러 추출 엔진을 병렬로 경합시켜 가능하면 워터마크 없는/원본 직링크를 반환하고 다운로드합니다.

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

**공개 UGC만 지원합니다.** 멤버십 / DRM 플랫폼(Tencent Video, iQIYI, Youku, Mango TV, Netflix, Disney+, HBO, Prime Video, Spotify, Hulu 등)은 엔진 실행 전에 거부됩니다. 로그인 탈취, 쿠키 피싱, WeChat Channels MITM은 하지 않습니다.

## 기능

- 웹 UI：`http://127.0.0.1:8787` — 공유 문구/URL 붙여넣기, 미리보기, 다운로드
- 다중 엔진 경합：먼저 성공한 추출기가 승리, 나머지는 취소
- 엔진：`share-page`, `douyin-browser`(헤드리스 Chrome), `yt-dlp`, `videofetch`, `you-get`, `webparser`, `lux`
- 공유 문구에서 첫 `http(s)` URL 추출
- 선택적 로컬 Netscape 쿠키 / `--cookies-from-browser`는 **최후 수단**(대신 가져오지 않음)
- VIP / DRM 호스트 명시적 차단; WeChat Channels 로그인/MITM 거부
- JSON API：parse, download, health, engines. OpenAPI：`/api/docs`

## 빠른 시작

```bash
cd video-unwatermark
chmod +x start.sh
./start.sh
```

Windows: `.\start.ps1` (또는 `start.bat`).

**http://127.0.0.1:8787** 을 엽니다.

수동 설치：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# optional: pip install videofetch you-get
python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
```

`ffmpeg`가 `PATH`에 있어야 합니다(yt-dlp 음/영상 병합):

```bash
# macOS
brew install ffmpeg
# Debian / Ubuntu
sudo apt-get install ffmpeg
# Windows
winget install --id Gyan.FFmpeg -e
```

`start.sh`(macOS/Linux) 또는 `start.ps1`(Windows)는 선택 엔진(`videofetch`, `you-get`, Playwright) 설치를 시도하고, 없으면 현재 OS/CPU용 `lux`를 `bin/`에 받습니다.

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/parse` | Body `{"url":"..."}` or multipart (`url`, optional `cookies_file`, `cookies_from_browser`) |
| `GET` | `/api/download?job=...` | Attachment download for a parse job |
| `GET` | `/api/preview?job=...` | Stream preview for a job |
| `GET` | `/api/health` | Engine + ffmpeg status; cookie flags only say *configured*, never contents |
| `GET` | `/api/engines` | Engine list |
| `GET` | `/api/docs` | OpenAPI UI |

성공 시 `ok`, `title`, `ext`, `filesize`, `thumbnail`, `extractor`, `platform`, `download_url`, `direct_url`, `preview_url`, `job`을 포함합니다. 게스트 차단 시 `{ok:false, needs_cookie:true, hint:"..."}`일 수 있습니다.

타임아웃：엔진당 약 25초, 전체 약 30초. Douyin/Kuaishou는 먼저 share-page + webparser + lux + `douyin-browser`(약 25초)를 경합하며, 전체 최대 약 95초.

## 지원 사이트와 제한

| Engine | Typical sites | Notes |
|---|---|---|
| **share-page** | Douyin, Kuaishou | Guest share-page HTML (`_ROUTER_DATA` / `__APOLLO_STATE__`); no login cookie |
| **douyin-browser** | Douyin | Headless Chrome; captures CDN `video_mp4` from `iesdouyin.com/share/video/{id}/` |
| **yt-dlp** | YouTube, Bilibili, TikTok, Instagram, X, Facebook, Reddit, Weibo, Vimeo, … | Follow [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) |
| **videofetch** | Douyin, Kuaishou, Xiaohongshu, Bilibili, … | Public-UGC clients only; VIP movie clients disabled |
| **you-get** | Some CN / social sites | Extra fallback parser |
| **webparser** | Douyin, Kuaishou | Keyless public JSON helpers (e.g. 17change, douyin.wtf hybrid) |
| **lux** | Douyin, Kuaishou | Local `bin/lux` binary; fallback only |

플랫폼 API는 자주 바뀌므로 실패는 정상입니다. 로그인이 필요한 콘텐츠는 `needs_cookie`를 반환할 수 있습니다.

**알려진 제한(솔직히):**

- **Douyin**: datacenter IPs often lack `play_addr` on share pages; yt-dlp may report `needs cookie`. Public hybrid parsers or `douyin-browser` may still succeed. Cookies are never stolen.
- **Kuaishou**: yt-dlp has no Kuaishou extractor. Existing `www.kuaishou.com/short-video/{id}` pages may parse via webparser; `v.kuaishou.com` shorts often expire; TLS EOF from some hosts is common.
- **Vimeo**: anonymous macos OAuth currently returns 401; use local `--cookies-from-browser` if you are logged in.
- **YouTube**: some IPs hit a bot wall (`Sign in to confirm you’re not a bot`); same optional local cookies apply.

## 선택적 쿠키(최후 수단)

일부 사이트(특히 Douyin / YouTube bot wall)는 데이터센터 익명 접근을 막습니다. 이 도구는 쿠키를 **대신 가져오지 않습니다**. 채팅에 쿠키를 붙여넣지 마세요.

**본인 PC**에서 **본인** Netscape 쿠키만 제공합니다：

1. **CLI**

```bash
./start.sh --cookies /path/to/cookies.txt
./start.sh --cookies-from-browser chrome
```

   `cookies_from_browser`는 해당 머신에 설치된 브라우저만 읽습니다. 원격 VPS에서는 무효입니다.

2. **환경 변수**

```bash
export UNWATERMARK_COOKIES=/path/to/cookies.txt
export UNWATERMARK_COOKIES_FROM_BROWSER=chrome   # optional, local only
./start.sh
```

3. **웹 / API** — 페이지에서 Local Cookies를 열고 Netscape `cookies.txt`를 업로드하거나 `cookies_from_browser`를 지정합니다. JSON 쿠키보내기는 거부됩니다.

업로드 파일은 해당 parse/download에만 쓰이며 외부 티켓 API로 보내지 않습니다.

## 아키텍처

FastAPI가 `static/`과 JSON을 제공합니다. `app/extract.py`가 단축 링크를 펼치고 차단 호스트를 거절한 뒤 단계별 엔진 경합을 실행합니다. 첫 성공이 단기 job을 만들고 `/api/download`가 파일을 저장합니다(필요 시 ffmpeg 병합). 상세：[../architecture.md](../architecture.md). 색인：[../README.md](../README.md).

## 기여

[../../CONTRIBUTING.md](../../CONTRIBUTING.md). 보안：[../../SECURITY.md](../../SECURITY.md). 변경 기록：[../../CHANGELOG.md](../../CHANGELOG.md).

## 라이선스

[Apache License 2.0](../../LICENSE) — Copyright 2026 652036. 서드파티 엔진은 각 라이선스를 유지합니다. [../../NOTICE](../../NOTICE) 참고.

## 면책

저장할 권리가 있는 공개 콘텐츠만 다운로드하고, 각 플랫폼 약관과 현지법을 지키세요. 이 프로젝트는 멤버십 크랙, DRM 복호화, 무단 접근을 **제공하지 않습니다**.
