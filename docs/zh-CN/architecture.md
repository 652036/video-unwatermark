# 架构说明

`video-unwatermark` 是一个小型 FastAPI 服务：把公开分享口令或链接解析成可下载的媒体文件。

## 请求流程

1. **界面 / API** — `static/` 挂在 `/`。`POST /api/parse` 支持 JSON 或 multipart（可选 Netscape Cookie）。
2. **归一化** — `app/extract.py`、`app/urls.py` 从分享口令抽出首个 `http(s)` 链接、展开短链，并拒绝 VIP/DRM 域名（`BLOCKED_HOSTS`）与微信视频号中间人式目标。
3. **分阶段竞速** — `app/engines/` 中可用引擎分阶段并行；抖音/快手先跑 `share-page` / `webparser` / `lux` / `douyin-browser`，避免 yt-dlp 的 `needs cookie` 吃光超时。先成功者胜出，其余取消。
4. **任务** — 成功后在 `app/jobs.py` 创建短期 job。
5. **落盘** — `/api/download`、`/api/preview` 由 `app/download.py` 拉取（必要时 ffmpeg 合并）。Cookie 仅经 `app/cookies.py` 作用域使用，不会替你去网站获取。

更细的英文说明见 [../architecture.md](../architecture.md)。

**仅公开 UGC。** 不做会员破解或 DRM 解密。
