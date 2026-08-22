# video-unwatermark

粘贴公开视频的分享口令或链接。服务端并行竞速多个解析引擎，返回无水印 / 原片直链，并支持预览与下载。

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

**仅支持公开 UGC 内容。** 腾讯视频、爱奇艺、优酷、芒果TV、Netflix、Disney+、HBO、Prime Video、Spotify、Hulu 等会员 / DRM 平台会在进入解析引擎前被拒绝。本项目不进行登录盗取、Cookie 钓鱼或微信视频号中间人采集。

## 功能

- Web 界面：`http://127.0.0.1:8787`，支持粘贴分享口令或链接进行预览与下载
- 多引擎并行竞速：优先采用最先成功的解析结果，其余任务自动取消
- 内置引擎：`share-page`、`douyin-browser`（无头 Chrome）、`yt-dlp`、`videofetch`、`you-get`、`webparser`、`lux`
- 自动从分享口令中提取首个 `http(s)` 链接
- 支持通过本机 Netscape 格式 Cookie 文件或 `--cookies-from-browser` 提供身份验证信息
- 明确拒绝 VIP / DRM 域名及微信视频号登录式采集
- 提供 JSON API（parse / download / health / engines），OpenAPI 文档位于 `/api/docs`

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

启动后访问 **http://127.0.0.1:8787**。

手动安装（任意系统）：

```bash
python3 -m venv .venv
# Windows: py -3 -m venv .venv && .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
# 可选：pip install videofetch you-get
python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
```

系统需安装 `ffmpeg`（用于 yt-dlp 合并音视频）：

```bash
# macOS
brew install ffmpeg

# Debian / Ubuntu
sudo apt-get install ffmpeg

# Windows（任选其一）
winget install --id Gyan.FFmpeg -e
# 或 choco install ffmpeg
```

`start.sh` / `start.ps1` 会自动安装可选引擎（`videofetch`、`you-get`、Playwright），并在缺失时下载对应平台的 `lux` v0.24.1（Linux / macOS / Windows，x86_64 或 arm64）至 `bin/` 目录。

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/parse` | 请求体 `{"url":"..."}` 或 multipart 表单（字段 `url`，可选 `cookies_file`、`cookies_from_browser`） |
| `GET` | `/api/download?job=...` | 按任务 ID 下载附件 |
| `GET` | `/api/preview?job=...` | 任务预览流 |
| `GET` | `/api/health` | 返回引擎与 ffmpeg 状态；仅报告 Cookie 是否已配置 |
| `GET` | `/api/engines` | 列出可用引擎 |
| `GET` | `/api/docs` | OpenAPI 交互式文档 |

成功响应包含：`ok`、`title`、`ext`、`filesize`、`thumbnail`、`extractor`、`platform`、`download_url`、`direct_url`、`preview_url`、`job`。若需要 Cookie，可能返回 `{ok:false, needs_cookie:true, hint:"..."}`。

超时设置：单引擎约 25 秒，整体约 30 秒；抖音 / 快手优先并发 `share-page` + `webparser` + `lux` + `douyin-browser`（约 25 秒），整体最长约 95 秒。

## 支持站点与限制

| 引擎 | 常见站点 | 说明 |
|---|---|---|
| **share-page** | 抖音、快手 | 解析游客分享页 HTML（`_ROUTER_DATA` / `__APOLLO_STATE__`），无需登录 Cookie |
| **douyin-browser** | 抖音 | 无头 Chrome，从 `iesdouyin.com/share/video/{id}/` 捕获 CDN `video_mp4` |
| **yt-dlp** | YouTube、B站、TikTok、Instagram、X、Facebook、Reddit、微博、Vimeo 等 | 以 [yt-dlp 官方支持列表](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) 为准 |
| **videofetch** | 抖音、快手、小红书、B站等 | 仅启用公开 UGC 客户端；会员影音相关客户端已禁用 |
| **you-get** | 部分国内 / 社交站点 | 额外兜底解析器 |
| **webparser** | 抖音、快手 | 无密钥公共 JSON 接口（如 17change、douyin.wtf hybrid） |
| **lux** | 抖音、快手 | 本地 `bin/lux` 二进制，作为兜底 |

平台接口可能变更，解析失败属正常情况。需要登录的内容可能返回 `needs_cookie`。

**已知限制：**

- **抖音**：机房 IP 访问分享页时可能缺少 `play_addr`；yt-dlp 可能提示需要 Cookie。公共 hybrid 接口或 `douyin-browser` 仍可能成功。
- **快手**：yt-dlp 暂无快手提取器。`www.kuaishou.com/short-video/{id}` 页面可由 webparser 解析；`v.kuaishou.com` 短链可能过期；部分环境可能出现 TLS EOF。
- **Vimeo**：匿名 macOS OAuth 当前返回 401；本机已登录时可使用 `--cookies-from-browser`。
- **YouTube**：部分 IP 可能触发 bot wall；可使用本机 Cookie。

## 可选 Cookie 配置

部分站点在匿名访问受限时需要身份验证信息。可使用本机 Netscape 格式 Cookie 文件，或通过 `--cookies-from-browser` 读取本地浏览器配置。

1. **启动参数**

```bash
# macOS / Linux
./start.sh --cookies /path/to/cookies.txt
./start.sh --cookies-from-browser chrome

# Windows PowerShell
.\start.ps1 -Cookies C:\path\to\cookies.txt
.\start.ps1 -CookiesFromBrowser chrome
```

`cookies_from_browser` 仅支持读取本机已安装浏览器的配置，远程环境无效。

2. **环境变量**

```bash
export UNWATERMARK_COOKIES=/path/to/cookies.txt
export UNWATERMARK_COOKIES_FROM_BROWSER=chrome
./start.sh
```

3. **Web 界面 / API**

在页面展开「本机 Cookies」，上传 Netscape 格式的 `cookies.txt`（可使用扩展 [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)），或指定 `cookies_from_browser`。不支持 JSON 格式 Cookie 导出。

Cookie 文件仅用于当前解析与下载任务。

## 架构

FastAPI 提供静态文件服务（`static/`）与 JSON 路由。`app/extract.py` 负责展开短链、拒绝黑名单域名，并分阶段并行竞速各引擎。首个成功结果写入短期 job；`/api/download` 负责文件落盘（必要时调用 ffmpeg 合并）。详见 [architecture.md](architecture.md) 与 [../architecture.md](../architecture.md)。文档索引：[../README.md](../README.md)。

## 参与贡献

请参阅 [../../CONTRIBUTING.md](../../CONTRIBUTING.md)。安全问题报告见 [../../SECURITY.md](../../SECURITY.md)。变更日志：[../../CHANGELOG.md](../../CHANGELOG.md)。

## 许可证

[Apache License 2.0](../../LICENSE) — Copyright 2026 652036。第三方引擎遵循各自许可证，详见 [../../NOTICE](../../NOTICE)。

## 免责声明

请仅下载有权保存的公开内容，并遵守各平台服务条款与当地法律法规。本项目不提供会员破解、DRM 解密或未授权访问功能。
