# 实测记录

测试时间：2026-08-18 13:55–14:02（Asia/Shanghai, UTC+8）  
测试方式：本机已启动的 `uvicorn`（`http://127.0.0.1:8787`）实际 `POST /api/parse`。  
规则：**只有本次跑通 parse 的站点才标通过。** 未登录、不偷 Cookie。

引擎：`yt-dlp 2026.07.04`、`videofetch 0.9.1`、`you-get 0.4.1743`，`ffmpeg` 在 PATH。  
`parse-video-py` 不在 PyPI，按「不 clone GitHub」跳过。

YouTube 短片「Me at the zoo」已走 `GET /api/download`：`downloads/Me at the zoo_188b46ab.mp4`，533915 字节，时长 19.06s，`ffprobe` 确认为 mp4。

## 结果表

| 站点 | 使用的 URL | 胜出引擎 | 结果 | 错误 / 备注 | 是否下载到文件 |
|---|---|---|---|---|---|
| 腾讯视频（拒绝名单） | `https://v.qq.com/x/cover/mzc00200foo/x.html` | — | **拒绝通过** | `不支持会员/DRM 平台：腾讯视频`（未调用提取器） | 否 |
| 爱奇艺（拒绝名单） | `https://www.iqiyi.com/v_1rr7p0h2w.html` | — | **拒绝通过** | `不支持会员/DRM 平台：爱奇艺` | 否 |
| Netflix（拒绝名单） | `https://www.netflix.com/watch/80057281` | — | **拒绝通过** | `不支持会员/DRM 平台：Netflix` | 否 |
| 抖音 Douyin | `https://www.douyin.com/video/7074193097323859241` 以及 `…/7014320659937447172` | — | **needs cookie** | 两枚公开页均返回 `needs cookie`（本机 IP / 游客被拦） | 否 |
| 哔哩哔哩 Bilibili | `https://www.bilibili.com/video/BV1Pkcbz3Ey8`（2026 拜年纪官方主线） | videofetch | **通过** | 标题：再一次的“初见”【2026拜年纪主线动画】 | 未下全片（解析成功） |
| 快手 Kuaishou | `https://www.kuaishou.com/f/X-1mzzENA9GVI2g1`、`https://v.kuaishou.com/2DV5QWg`、`https://www.kuaishou.com/short-video/3xbfgiys9bhs9em` | — | **失败** | yt-dlp 无快手提取器 / 超时；you-get 失败；videofetch 超时。短链样本可能已失效 | 否 |
| 小红书 Xiaohongshu | `https://www.xiaohongshu.com/explore/672451ee000000001a034bc6` | you-get | **通过** | 标题为一串 hash；ext=mp4，约 897 KB | 未下全片 |
| 微博 Weibo | `https://weibo.com/6868583654/RcpUlAGpL`（北京广播电视台公开微博视频） | yt-dlp | **通过** | 标题：北京广播电视台的微博视频；约 22.6 MB | 未下全片 |
| YouTube | `https://www.youtube.com/watch?v=jNQXAC9IVRw`（第一支 YouTube 片，19s） | yt-dlp | **通过** | Me at the zoo | **是**，533915 B |
| TikTok | `https://www.tiktok.com/@tiktok/video/7308939429790502190`（官方账号 YearOnTikTok） | yt-dlp | **通过** | 官方回顾片标题截断可见 | 未下全片 |
| Instagram | `https://www.instagram.com/nasa/reel/DH_hyJbprmG/`（NASA 公开 Reel） | yt-dlp | **通过** | Video by nasa | 未下全片 |
| Twitter / X | `https://twitter.com/i/status/1780333914730496488` | you-get | **通过** | ext=mp4，约 27.3 MB。另一条 NASA 图文推文正确报「No video」 | 未下全片 |
| Facebook | `https://www.facebook.com/facebook/videos/10153231379946729/`（Facebook 官方公开片） | yt-dlp | **通过** | How to Share With Just Friends | 未下全片 |
| Reddit | `https://www.reddit.com/r/geese/comments/1slctzu/she_hatched_all_seven_eggs_she_sat_on/` | yt-dlp | **通过** | She Hatched All SEVEN Eggs She Sat On；约 17.5 MB | 未下全片 |
| Vimeo | `https://vimeo.com/163736810`、`https://vimeo.com/1084537`（Big Buck Bunny）、`https://vimeo.com/76979871` | — | **失败** | yt-dlp：`Failed to fetch macos OAuth token: HTTP Error 401`（机房 IP 常见）；you-get 失败 | 否 |

## 小结

- **解析通过**：Bilibili、小红书、微博、YouTube、TikTok、Instagram、X、Facebook、Reddit。
- **实际落盘**：YouTube「Me at the zoo」。
- **needs cookie**：抖音（本环境游客访问被拦，不假装成功）。
- **失败**：快手（无 yt-dlp 提取器 + 样本链失效/超时）、Vimeo（OAuth 401）。
- **拒绝名单**：腾讯视频 / 爱奇艺 / Netflix 在进引擎前干净失败。

原始 JSON：`smoke_results.json`、`smoke_retry.json`、`smoke_retry2.json`。

---

# 复测（抖音 / 快手改进后）

测试时间：2026-08-18 14:10–14:14（Asia/Shanghai, UTC+8）  
测试方式：重启后的 `uvicorn`（`http://127.0.0.1:8787`）实际 `POST /api/parse`。  
规则：**只有本轮跑通 parse 才标通过。** 未登录、不偷 Cookie。

引擎：`share-page`、`yt-dlp 2026.07.04`、`videofetch 0.9.1`、`you-get 0.4.1743`、`webparser`、`lux 0.24.1`。  
本轮新增：分享页 URL 归一化（`v.douyin.com` / `iesdouyin.com` / aweme id；`v.kuaishou.com` / `short-video`）、快手 videofetch 只走 requests（跳过 DrissionPage）、可选 Netscape cookies / `cookies_from_browser`。

## 本轮结果

| 站点 | 使用的 URL | 胜出引擎 | 结果 | 错误 / 备注 | 是否下载到文件 |
|---|---|---|---|---|---|
| 腾讯视频（拒绝名单） | `https://v.qq.com/x/cover/mzc00200foo/x.html` | — | **拒绝通过** | 进引擎前拒绝，VIP 名单仍有效 | 否 |
| 抖音 iesdouyin 分享页 | `https://www.iesdouyin.com/share/video/7675153416574974784`（2026-08-18 公开片） | — | **needs cookie** | 分享页有 `_ROUTER_DATA` 但无 `videoInfoRes`/`play_addr`；iteminfo/detail API 空体或 403。本机 IP 游客解析做不到 | 否 |
| 抖音 www | `https://www.douyin.com/video/7675153416574974784` | — | **needs cookie** | 同上；已自动改写 iesdouyin 再试 | 否 |
| 抖音 旧 ID | `https://www.douyin.com/video/7074193097323859241` | — | **needs cookie** | 14:10 复测，仍游客被拦 | 否 |
| 快手 现存网页 | `https://www.kuaishou.com/short-video/3xzi7vetekkan4s` | webparser | **通过** | 标题：全北京寻找地道的车主和车并接受挑战第二期…；有直链。23.8s | 未下全片 |
| 快手 旧短链 | `https://v.kuaishou.com/2DV5QWg` → `3xbfgiys9bhs9em` | — | **失败** | SSL unexpected EOF；gifshow 无 CDN。短链样本失效/机房 TLS 不稳 | 否 |
| Vimeo | `https://vimeo.com/163736810` | — | **失败** | yt-dlp macos OAuth 401（机房 IP，无简单匿名修复） | 否 |
| YouTube 回归 | `https://www.youtube.com/watch?v=jNQXAC9IVRw` | — | **needs cookie** | 本轮 yt-dlp：`Sign in to confirm you’re not a bot`。上一轮（14:00 前）曾通过并落盘，本轮机房 IP 被 YouTube 拦 | 否 |
| 哔哩哔哩 回归 | `https://www.bilibili.com/video/BV1Pkcbz3Ey8` | videofetch | **通过** | 再一次的“初见”【2026拜年纪主线动画】 | 未下全片 |
| cookies 校验 | JSON 上传 | — | **拒绝通过** | 明确要求 Netscape，拒绝 JSON cookie 导出 | — |

## 本轮小结

- **新通过**：快手现存 `short-video/3xzi7vetekkan4s`（webparser）。
- **仍 needs cookie**：抖音（iesdouyin 分享页已不再内嵌作品 JSON；本环境无游客直链）。可选本机 `--cookies` / 上传 Netscape / `cookies_from_browser`。
- **仍失败**：过期快手短链、Vimeo OAuth 401。
- **VIP 名单**：腾讯视频仍干净拒绝。
- **回归**：Bilibili 仍通过。YouTube 本轮被 bot wall，不改写上一轮落盘记录。

原始 JSON：`smoke_round3.json`、`smoke_round3b.json`。

---

# 实测记录（cookie-free 引擎，2026-08-18 14:13–14:22 Asia/Shanghai）

测试时间：2026-08-18 14:13–14:22（UTC+8）  
方式：重启后的 `uvicorn` `http://127.0.0.1:8787` 实际 `POST /api/parse`。  
规则：只有本次跑通 parse 才标通过。未登录、不提供 Cookie。

新增引擎：`share-page`（iesdouyin / 快手分享页）、`webparser`（17change `/parse/video`）、`lux 0.24.1`（`bin/lux` Linux amd64 release）。  
竞速顺序：抖音/快手先 share-page，再 yt-dlp / videofetch / you-get，最后 webparser / lux。Cookie 只作为失败后的可选提示。

公开样本来源：WebSearch 到的 2026 辽宁春晚快手宣发片、抖音索引页 `7670825424041069843`（2026-08-06）、以及上一轮已通过的 B 站拜年纪主线。

## 结果表

| 站点 | 使用的 URL | 胜出引擎 | 结果 | 错误 / 备注 | 是否下载到文件 |
|---|---|---|---|---|---|
| 快手 Kuaishou | `https://www.kuaishou.com/short-video/3x9vcycq5g3p2y9`（辽宁卫视 #2026辽宁春晚官宣） | webparser | **通过** | 标题含「跟着马上把新年福气装进口袋」；`direct_url` 为 `tymov2.a.kwimgs.com` mp4。share-page 对本机访问 `kuaishou.com`/`gifshow.com` 多次 SSL EOF，未抢到胜出；17change 前端 JSON 接口可用。约 19s | 否（解析成功，有直链） |
| 抖音 Douyin | `https://www.douyin.com/video/7670825424041069843` | — | **失败** | share-page：`iesdouyin.com/share/video/{id}` 有 `_ROUTER_DATA` 但无 `videoInfoRes`/`play_addr`（空壳 SSR）。webparser：17change 回报「抖音页面结构可能已变化」。lux：JSON 不可用。yt-dlp 报登录墙。本环境未假装成功 | 否 |
| 哔哩哔哩 Bilibili（回归） | `https://www.bilibili.com/video/BV1Pkcbz3Ey8`（2026 拜年纪官方主线） | videofetch | **通过** | 标题：再一次的“初见”【2026拜年纪主线动画】。新引擎 `matches()` 不接 B 站，未破坏原有竞速 | 否 |

## 本轮小结

- **解析通过**：快手（webparser / 17change，无 Cookie）、Bilibili（videofetch）。
- **失败**：抖音。机房 IP 上官方分享页不再内嵌 `play_addr`；公共解析站同样认不出。已实现 playwm→play、多套手机 UA、`RENDER_DATA`/`discover?modal_id`，本次样本仍无视频 JSON。
- **YouTube 回归未标通过**：本机 IP 对 `jNQXAC9IVRw` 返回 yt-dlp「Sign in to confirm you’re not a bot」。与本次引擎改动无关，不记为通过。
- **跳过的公共站**：v2ob（`NEXT_PUBLIC_PARSER_API_URL` 未配置）、snapany（官方 extract 要开发者 key）、hellotik（`/api/parse` 需 parseTicket 加密）。
- **lux**：已放入 `bin/lux`（v0.24.1 Linux x86_64 release）。对本快手样本超时，对抖音无可用 JSON。

原始 JSON：`smoke_round2.json`、`smoke_round3.json`。

---

# 复测（抖音公共解析 + 阶段顺序，2026-08-18 14:21–14:22 Asia/Shanghai）

测试时间：2026-08-18 14:21–14:22（UTC+8；UTC 06:21–06:22）  
测试方式：重启后的 `uvicorn`（`http://127.0.0.1:8787`）实际 `POST /api/parse`。  
规则：**只有本轮 parse 返回了直链才标通过。** 未登录、不偷 Cookie。

改动：抖音/快手第一轮就把 webparser + lux 和 share-page 一起竞速；yt-dlp 的 `needs cookie` 不再吃掉整体超时。webparser 没拿到满 15 秒时不会用 `needs cookie` 收场。公共 JSON 增加 Evil0ctal `https://douyin.wtf/api/hybrid/video_data`、yujn `/api/dy_jx.php`、tenapi `/v2/video`（tenapi 本轮 502）。SnapAny 要开发者 key、V2OB 的 `NEXT_PUBLIC_PARSER_API_URL` 仍为空，已跳过。不会把抖音 ID 猜成 TikTok（tikwm 对抖音 URL 直接报 `Url parsing is failed`）。

引擎：`share-page`、`yt-dlp 2026.07.04`、`videofetch 0.9.1`、`you-get 0.4.1743`、`webparser 17change+douyin.wtf+yujn+tenapi`、`lux 0.24.1`。

## 本轮结果

| 站点 | 使用的 URL | 胜出引擎 | 结果 | 错误 / 备注 | 是否下载到文件 |
|---|---|---|---|---|---|
| 抖音 分享口令 | `6.41 08/18 … https://v.douyin.com/J4IQiholWbo/ 复制此链接…` | webparser | **通过** | 标题：爱情公寓｜第三季｜第257集。直链 `aweme.snssdk.com/aweme/v1/play/?video_id=v0d00fg10000d787jq7og65p3g4j12r0`。7.14s | 否（解析成功，有直链） |
| 抖音 iesdouyin | `https://www.iesdouyin.com/share/video/7675153416574974784` | webparser | **通过** | 标题：管她美的像不像…。直链 `…/play/?video_id=v0200fg10000da1psqfog65suitu4ohg`。20.03s | 否 |
| 抖音 www | `https://www.douyin.com/video/7675153416574974784` | webparser | **通过** | 同上作品，1.96s | 否 |
| 快手 short-video | `https://www.kuaishou.com/short-video/3xzi7vetekkan4s` | webparser | **通过** | 标题：全北京寻找地道的车主和车…；`hwmov.a.yximgs.com` mp4。1.43s。无回归 | 否 |
| 哔哩哔哩 回归 | `https://www.bilibili.com/video/BV1Pkcbz3Ey8` | videofetch | **通过** | 再一次的“初见”【2026拜年纪主线动画】。5.80s。无回归 | 否 |

## 原始公共解析响应（未改 Cookie；set-cookie 均为空）

**17change** `POST https://api4.17change.cn/parse/video` 对上面两条抖音 URL 均为 HTTP 200：

```json
{"code":5001,"name":"parse","title":"短视频去水印","message":"解析失败，抖音页面结构可能已变化，请稍后重试"}
```

所以 17change **不是**本轮抖音通过的原因；阶段顺序修复让 `douyin.wtf` 能在第一轮跑完。快手仍走 17change。

**douyin.wtf** `GET https://douyin.wtf/api/hybrid/video_data?url=…&minimal=true`：`api.douyin.wtf` 是 404，活着的是 `douyin.wtf`。两条样本都是 HTTP 200、`code=200`，关键字段：

- `v.douyin.com/J4IQiholWbo/` → `video_id=7624728488368732900`，`desc=爱情公寓｜第三季｜第257集`，`video_data.nwm_video_url=https://aweme.snssdk.com/aweme/v1/play/?video_id=v0d00fg10000d787jq7og65p3g4j12r0&ratio=1080p&line=0`
- `iesdouyin.com/share/video/7675153416574974784` → `video_id=7675153416574974784`，`nwm_video_url=https://aweme.snssdk.com/aweme/v1/play/?video_id=v0200fg10000da1psqfog65suitu4ohg&ratio=1080p&line=0`

完整原文见 `smoke_round4.json` 的 `raw_probes`（含 author/music/cover，无 Cookie）。

其它本轮探测：yujn `/api/dy_jx.php` 返回「请求频繁或稍后再试」；tenapi `/v2/video` Cloudflare 502；tikwm 对抖音 URL `code=-1 Url parsing is failed`（未接入）。

## 本轮小结

- **新通过**：抖音分享口令、iesdouyin、www（webparser / douyin.wtf，均有直链）。
- **无回归**：快手 `3xzi7vetekkan4s`、Bilibili 拜年纪主线。
- **17change 对抖音仍失败**（code 5001）；阶段 bug 修掉后公共 hybrid 接口能先跑完。
- **跳过**：SnapAny（要 key）、V2OB（无公开 parser URL）、hellotik（加密 ticket）、TikTok 双开猜测。

原始 JSON：`smoke_round4.json`。

---

# 实测记录（douyin-browser 网络抓取，2026-08-18 14:30–14:33 Asia/Shanghai）

测试时间：2026-08-18 14:30–14:33（UTC+8；UTC 06:30–06:33）  
方式：重启后的 `uvicorn` `http://127.0.0.1:8787` 实际 `POST /api/parse`；另对 `douyin-browser` 做了单引擎隔离。  
规则：**只有本次 parse 返回了视频直链才标通过。** 未登录、不偷用户 Cookie、不点登录框。

新增引擎：`douyin-browser`（`app/engines/douyin_browser.py`，name=`douyin-browser`，stage=15）。  
Playwright 1.62.0 + 本机 `/usr/bin/google-chrome` 151.0.7922.71，headless，`--no-sandbox`。未 `playwright install chromium`（系统 Chrome 已可用）。  
打开 `https://www.iesdouyin.com/share/video/{aweme_id}/`（**必须带尾斜杠**），监听 request/response + `performance.getEntriesByType('resource')`，收集 `zjcdn` / `douyinvod` / `bytecdn` / `tos-cn-v-` / `mime_type=video_mp4` / `/aweme/v1/play`，排除 `douyinstatic` UI mp4 和 aweme detail JSON。Range GET（抖音 Referer + 手机 UA）必须 206/200。登录 QR 不点击。

`extract.py`：抖音在 yt-dlp `needs_cookie` 收场前必须跑完或超时 `douyin-browser`（第一轮与 share-page/webparser 竞速，预算 25s；另有 last-chance）。

## 本轮结果

| 站点 | 使用的 URL | 胜出引擎 | 结果 | 错误 / 备注 | 是否下载到文件 |
|---|---|---|---|---|---|
| 抖音 www | `https://www.douyin.com/video/7670825424041069843` | webparser | **通过** | 标题：家长一定要告诉孩子，人民日报是考场作文的风向标，也是语文阅读理解素材的重要来源。`ok=true` `direct_url` host=`aweme.snssdk.com` path=`/aweme/v1/play/` `video_id=v03033g10000d9q3u6fog65n1hgofb5g`。2.53s。Range GET `206` 2 097 152 B，最终 host=`v3-dy-o.zjcdn.com` | 抽了 2 MB（未下全片） |
| 抖音 iesdouyin | `https://www.iesdouyin.com/share/video/7670825424041069843/` | webparser | **通过** | 同上作品。2.11s。`direct_url` host=`aweme.snssdk.com` | 否（与上条同一 play 接口） |
| 快手 short-video | `https://www.kuaishou.com/short-video/3x9vcycq5g3p2y9` | webparser | **通过** | 辽宁春晚官宣；`tymov2.a.kwimgs.com` mp4。0.25s。无回归 | 否 |

`GET /api/health`：`douyin-browser` available=`true` version=`playwright-1.62.0`。

## 单引擎隔离（douyin-browser）

对 `https://www.iesdouyin.com/share/video/7670825424041069843/` 直接 `DouyinBrowserEngine.extract`（14:30 UTC+8）：

- `ok=true`，engine=`douyin-browser`
- 候选 host：`v5-dy-ov-experiment.zjcdn.com`、`v3-web-prime.douyinvod.com`、`lf-douyin-mobile.bytecdn.com`
- 胜出：`v5-dy-ov-experiment.zjcdn.com`，path 含 `video/tos/cn/tos-cn-vd-…`，query `mime_type=video_mp4`，非 `playwm`
- Range GET `206` 2048 B
- 耗时 25.76s（桌面页先听网络，再 mobile 上下文抓到 CDN）
- 本轮 API 竞速被更快的 `webparser`/`douyin.wtf` 抢到胜出，**未假装 browser 是 API 胜出引擎**

## 本轮小结

- **解析通过**：抖音 www / iesdouyin（webparser，有直链）、快手（webparser，无回归）。
- **Playwright/Chrome**：可用。headless 系统 Chrome 能抓到任务描述里的 `v5-dy-ov-experiment.zjcdn.com` + `mime_type=video_mp4`。
- **needs_cookie**：本轮未触发。`extract.py` 在 `douyin-browser` 跑完/超时前不会用这句话收场。
- **未登录**，未读用户 Chrome Cookie。

原始 JSON：`smoke_round5.json`。
