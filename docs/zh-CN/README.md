# video-unwatermark

粘贴**公开**视频分享口令或链接。服务端并行竞速多个解析引擎，尽量返回无水印 / 原片直链并下载。

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

**仅支持公开 UGC。** 腾讯视频、爱奇艺、优酷、芒果、Netflix、Disney+、HBO、Prime Video、Spotify、Hulu 等会员 / DRM 平台会在进入引擎前被拒绝。不做登录盗取、Cookie 钓鱼或微信视频号中间人。

## 功能

- Web 界面：`http://127.0.0.1:8787` — 粘贴分享口令或链接，预览并下载
- 多引擎竞速：先成功者胜出，其余取消
- 引擎：`share-page`、`douyin-browser`（无头 Chrome）、`yt-dlp`、`videofetch`、`you-get`、`webparser`、`lux`
- 可从分享口令正则抽出首条 `http(s)` 链接
- 可选本机 Netscape Cookie / `--cookies-from-browser` 作为**最后手段**（不会替你获取）
- 明确拒绝 VIP / DRM 域名；拒绝视频号登录中间人式采集
- JSON API：parse / download / health / engines，OpenAPI 见 `/api/docs`

## 快速开始

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
# 或: start.bat
```

浏览器打开 **http://127.0.0.1:8787**。

手动安装（任意系统）：

```bash
python3 -m venv .venv
# Windows: py -3 -m venv .venv && .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
# optional: pip install videofetch you-get
python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
```

系统需有 `ffmpeg`（yt-dlp 合并音视频）：

```bash
# macOS
brew install ffmpeg

# Debian / Ubuntu
sudo apt-get install ffmpeg

# Windows（任选其一；可能需要管理员权限）
winget install --id Gyan.FFmpeg -e
# choco install ffmpeg
```

`start.sh` / `start.ps1` 会尝试安装可选引擎（`videofetch`、`you-get`、Playwright），并在缺少时按当前系统自动下载对应平台的 `lux` v0.24.1（Linux / macOS / Windows，x86_64 或 arm64）到 `bin/`。

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/parse` | Body `{"url":"..."}` 或 multipart（`url`，可选 `cookies_file`、`cookies_from_browser`） |
| `GET` | `/api/download?job=...` | 按任务附件下载 |
| `GET` | `/api/preview?job=...` | 任务预览流 |
| `GET` | `/api/health` | 引擎与 ffmpeg 状态；Cookie 只报是否已配置，不回传内容 |
| `GET` | `/api/engines` | 引擎列表 |
| `GET` | `/api/docs` | OpenAPI 文档 |

成功返回含 `ok`、`title`、`ext`、`filesize`、`thumbnail`、`extractor`、`platform`、`download_url`、`direct_url`、`preview_url`、`job`。游客被拦时可能为 `{ok:false, needs_cookie:true, hint:"..."}`。

超时：单引擎约 25 秒，整体约 30 秒；抖音/快手先并发分享页 + webparser + lux + `douyin-browser`（约 25 秒），整体最多约 95 秒。

## 支持站点与限制

| 引擎 | 常见站点 | 说明 |
|---|---|---|
| **share-page** | 抖音、快手 | 游客分享页 HTML（`_ROUTER_DATA` / `__APOLLO_STATE__`）；不要求登录 Cookie |
| **douyin-browser** | 抖音 | 无头 Chrome，从 `iesdouyin.com/share/video/{id}/` 抓 CDN `video_mp4` |
| **yt-dlp** | YouTube、B站、TikTok、Instagram、X、Facebook、Reddit、微博、Vimeo 等 | 以 [yt-dlp 支持列表](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) 为准 |
| **videofetch** | 抖音、快手、小红书、B站等 | 仅公开 UGC 客户端；会员影音客户端已禁用 |
| **you-get** | 部分国内 / 社交站点 | 额外兜底 |
| **webparser** | 抖音、快手 | 无密钥公共 JSON（如 17change、douyin.wtf hybrid） |
| **lux** | 抖音、快手 | 本地 `bin/lux`；兜底 |

平台接口经常变，解析失败是正常现象。需要登录的内容可能返回 `needs_cookie`。

**已知限制（诚实记录）：**

- **抖音**：机房 IP 上分享页常无 `play_addr`；yt-dlp 可能报 `needs cookie`。公共 hybrid 或 `douyin-browser` 仍可能成功。不会去偷 Cookie。
- **快手**：yt-dlp 无快手提取器。现存 `www.kuaishou.com/short-video/{id}` 可由 webparser 解析；`v.kuaishou.com` 短链常过期；部分环境会 TLS EOF。
- **Vimeo**：匿名 macos OAuth 目前 401；本机已登录可用 `--cookies-from-browser`。
- **YouTube**：部分 IP 会遇 bot wall；同样走可选本机 Cookie。

## 可选 Cookies（最后手段）

部分站点（尤其抖音 / YouTube bot wall）会拦截机房游客访问。本工具**不会**替你获取 Cookie。**不要**把 Cookie 粘贴到聊天里。

只在你自己的电脑上提供**你自己的** Netscape Cookie：

1. **启动参数**

```bash
# macOS / Linux
./start.sh --cookies /path/to/cookies.txt
./start.sh --cookies-from-browser chrome

# Windows PowerShell
.\start.ps1 -Cookies C:\path\to\cookies.txt
.\start.ps1 -CookiesFromBrowser chrome
```

   `cookies_from_browser` 只能读**本机**已安装浏览器。远程服务器无你的浏览器配置时无效。

2. **环境变量**

```bash
export UNWATERMARK_COOKIES=/path/to/cookies.txt
export UNWATERMARK_COOKIES_FROM_BROWSER=chrome   # optional, local only
./start.sh
```

3. **网页 / API** — 展开「本机 Cookies」，上传 Netscape `cookies.txt`（可用扩展 [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)），或选择 `cookies_from_browser`。拒绝 JSON 格式 Cookie 导出。

文件仅用于当次解析/下载，不会拿去外站换票。

## 架构

FastAPI 提供 `static/` 与 JSON 路由。`app/extract.py` 展开短链、拒绝黑名单域名，再分阶段竞速引擎。首个成功结果写入短期 job；`/api/download` 负责落盘（必要时 ffmpeg 合并）。详见 [architecture.md](architecture.md) 与 [../architecture.md](../architecture.md)。文档索引：[../README.md](../README.md)。

## 参与贡献

见 [../../CONTRIBUTING.md](../../CONTRIBUTING.md)。安全报告：[../../SECURITY.md](../../SECURITY.md)。变更记录：[../../CHANGELOG.md](../../CHANGELOG.md)。

## 许可证

[Apache License 2.0](../../LICENSE) — Copyright 2026 652036。第三方引擎仍遵循各自许可证，见 [../../NOTICE](../../NOTICE)。

## 免责声明

请只下载你有权保存的公开内容，并遵守各平台条款与当地法律。本项目**不提供**会员破解、DRM 解密或未授权访问。
