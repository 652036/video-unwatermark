# 无水印解析下载

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

粘贴公开视频分享口令或链接，服务端并行调用多个解析引擎，提取尽量无水印 / 原片的直链并下载。

**仅支持公开 UGC。** 腾讯视频、爱奇艺、优酷、芒果、Netflix、Disney+、HBO、Prime Video、Spotify 等会员 / DRM 平台会被直接拒绝。不做登录盗取、Cookie 钓鱼或微信视频号中间人。

## 如何运行

```bash
cd video-unwatermark
chmod +x start.sh
./start.sh
```

浏览器打开 `http://127.0.0.1:8787`。

手动方式：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 可选：pip install videofetch you-get
python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
```

需要系统里有 `ffmpeg`（yt-dlp 合并音视频用）。Debian/Ubuntu：`sudo apt-get install ffmpeg`。

## 最后手段：本机 Cookies（仅当分享页 / 兜底仍失败）

部分站点（尤其是抖音）会从机房 IP 拦截游客解析，返回 `needs cookie`。本工具**不会**替你去网站拿 Cookie，也**不要**把 Cookie 粘贴到聊天里。

只在你自己的电脑上，用下列任一方式提供**你自己**的 Netscape cookies：

1. **启动参数**（等价于 yt-dlp `--cookies` / `--cookies-from-browser`）

   ```bash
   ./start.sh --cookies /path/to/cookies.txt
   ./start.sh --cookies-from-browser chrome
   ```

   `cookies_from_browser` 只能读**本机**已安装浏览器的登录态（chrome / chromium / firefox / edge / brave / safari 等）。在远程服务器上无效。

2. **环境变量**

   ```bash
   export UNWATERMARK_COOKIES=/path/to/cookies.txt
   export UNWATERMARK_COOKIES_FROM_BROWSER=chrome   # 可选，仅本机
   ./start.sh
   ```

3. **网页 / API**

   - 页面可展开「本机 Cookies」，上传 Netscape `cookies.txt`（可用扩展 [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) 自行导出），或选择 `cookies_from_browser`。
   - `POST /api/parse` JSON：`{"url":"...","cookies_path":"/abs/path/cookies.txt","cookies_from_browser":"chrome"}`
   - 或 `multipart/form-data` 字段：`url`、`cookies_file`（文件）、`cookies_from_browser`

不要上传 JSON 格式的 Cookie 导出。文件只在本次解析/下载中使用，不会去外站换票。

## API

- `POST /api/parse`  body `{"url":"..."}` — 可从分享口令里正则抽出第一条 http(s) 链接
- 返回 `{ok, title, ext, filesize, thumbnail, extractor, platform, download_url, direct_url}`
- 游客被拦时：`{ok:false, needs_cookie:true, hint:"..."}`
- `GET /api/download?job=...` — 按文件名附件下载
- `GET /api/health` — 引擎与 ffmpeg 状态；`cookies.file_configured` / `cookies.browser_configured` 只报是否已配置，不回传内容
- `GET /api/engines` — 引擎列表

解析超时：单引擎约 25 秒，整体约 30 秒；抖音/快手先并发分享页 + webparser + lux，再跑 `douyin-browser`（约 25 秒），整体最多约 95 秒。多引擎并行，先成功者胜出，其余取消。yt-dlp 的 `needs cookie` 不会挡住 webparser / douyin-browser：抖音在浏览器引擎跑完或超时前不会用这句话收场。

## 支持站点

- **douyin-browser（抖音，stage 15）**：无登录 headless Chrome。打开 `iesdouyin.com/share/video/{id}/`（必须带尾斜杠），从网络/Performance 抓 `zjcdn` / `mime_type=video_mp4` 直链，Range GET 校验。不点登录框、不读用户 Cookie。
- **share-page（抖音/快手先发）**：从分享口令抽出 aweme / photoId，跟 `v.douyin.com` / `v.kuaishou.com` 短链。抖音用手机 UA 拉 `iesdouyin.com/share/video/{id}`，解析 `_ROUTER_DATA` / `RENDER_DATA`，`playwm`→`play`。快手跟到分享页后解析 `__APOLLO_STATE__` / `INIT_STATE` / `<video src>` / CDN mp4。不依赖登录 Cookie。
- **yt-dlp**：1700+ 站点（YouTube、B站、TikTok、Instagram、X、Facebook、Reddit、Vimeo、微博等），以 [yt-dlp 支持列表](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) 为准。
- **videofetch (videodl)**：国内短视频补强（抖音、快手、小红书、B站等），已禁用其会员站客户端。
- **you-get**：部分国内站的额外解析器
- **webparser（抖音/快手先发 + 兜底）**：与分享页同一轮竞速，再在 yt-dlp `needs cookie` 之后仍会再跑一轮。简单无密钥 JSON：17change `/parse/video`、Evil0ctal `douyin.wtf/api/hybrid/video_data`、yujn `/api/dy_jx.php`、tenapi `/v2/video`。v2ob / snapany / hellotik 未暴露无密钥简单接口，已跳过。不会把抖音 ID 猜成 TikTok。
- **lux（兜底）**：`bin/lux`（GitHub release 的 Linux amd64 资产，不是 git clone），只对抖音/快手 URL 调用。

平台接口经常变，解析失败是正常现象。需要登录的内容会返回 `needs cookie`。

**已知限制（诚实记录）：**

- 抖音：机房 IP 上分享页 `_ROUTER_DATA` 往往没有 `play_addr`，yt-dlp 会 `needs cookie`。本轮会先并发打公共 JSON（17change 对抖音目前 5001；`douyin.wtf` hybrid 仍可能给出 `nwm_video_url`）。不会去偷 Cookie。
- 快手：yt-dlp 没有快手提取器。现存 `www.kuaishou.com/short-video/{id}` 可由 webparser 解析；`v.kuaishou.com` 短链常过期，且机房访问 kuaishou.com 会偶发 TLS EOF。登录墙时仍可能 `needs cookie`。
- Vimeo：匿名 macos OAuth 已 401，没有不登录的简单修复。本机已登录时可用 `--cookies-from-browser` + web client。
- YouTube：机房 IP 可能 bot wall（`Sign in to confirm you’re not a bot`），同样走可选本机 cookies。

## 免责声明

请只下载你有权保存的公开内容，并遵守各平台条款与当地法律。本项目不提供会员破解、DRM 解密或未授权访问。

实测记录见 [TEST.md](TEST.md)。
