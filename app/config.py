"""App constants. VIP/DRM hosts are refused before any extractor runs."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = ROOT / "downloads"
STATIC_DIR = ROOT / "static"
COOKIE_UPLOAD_DIR = DOWNLOAD_DIR / ".cookies"
LUX_BIN = ROOT / "bin" / "lux"

ENGINE_TIMEOUT = 25.0
OVERALL_TIMEOUT = 30.0
SHARE_TIMEOUT = 12.0
BROWSER_TIMEOUT = 25.0
CN_OVERALL_TIMEOUT = 95.0
DOWNLOAD_TIMEOUT = 180.0
MAX_DOWNLOAD_BYTES = 800 * 1024 * 1024

# Optional local cookies. Never fetched from a website.
# Netscape file: UNWATERMARK_COOKIES=/path/to/cookies.txt
# Browser (this machine only): UNWATERMARK_COOKIES_FROM_BROWSER=chrome
COOKIES_FILE = (os.environ.get("UNWATERMARK_COOKIES") or os.environ.get("COOKIES_FILE") or "").strip() or None
COOKIES_FROM_BROWSER = (
    os.environ.get("UNWATERMARK_COOKIES_FROM_BROWSER") or os.environ.get("COOKIES_FROM_BROWSER") or ""
).strip() or None

BROWSER_CHOICES = (
    "chrome",
    "chromium",
    "firefox",
    "edge",
    "brave",
    "opera",
    "safari",
    "vivaldi",
    "whale",
)

# hostname suffix -> display name. Matched on hostname (and sometimes path).
BLOCKED_HOSTS: dict[str, str] = {
    "v.qq.com": "腾讯视频",
    "film.qq.com": "腾讯视频",
    "wetv.vip": "腾讯视频",
    "wetv.video": "腾讯视频",
    "iqiyi.com": "爱奇艺",
    "iq.com": "爱奇艺",
    "youku.com": "优酷",
    "soku.com": "优酷",
    "mgtv.com": "芒果TV",
    "hunantv.com": "芒果TV",
    "netflix.com": "Netflix",
    "disneyplus.com": "Disney+",
    "disney.com": "Disney+",
    "hbo.com": "HBO",
    "hbomax.com": "HBO",
    "max.com": "HBO",
    "primevideo.com": "Prime Video",
    "spotify.com": "Spotify",
    "hulu.com": "Hulu",
}

# 视频号: refuse login/MITM style capture
WECHAT_CHANNELS_HINTS = (
    "channels.weixin.qq.com",
    "weixin.qq.com/sph",
    "weixin.qq.com/tv",
)

# videofetch/videodl: only public-UGC site clients. No VIP movie clients.
VIDEOFETCH_ALLOW = [
    "DouyinVideoClient",
    "KuaishouVideoClient",
    "RednoteVideoClient",
    "WeiboVideoClient",
    "BilibiliVideoClient",
    "YouTubeVideoClient",
    "RedditVideoClient",
    "WeishiVideoClient",
    "XiguaVideoClient",
    "PipixVideoClient",
    "AcFunVideoClient",
    "HaokanVideoClient",
    "ZhihuVideoClient",
    "BaiduTiebaVideoClient",
    "MeipaiVideoClient",
    "ZuiyouVideoClient",
    "PipigaoxiaoVideoClient",
    "TedVideoClient",
    "DailyMotionVideoClient",
    "OasisVideoClient",
    "SinaVideoClient",
    "XinpianchangVideoClient",
    "PearVideoClient",
    "DuxiaoshiVideoClient",
    "HuyaVideoClient",
    "SixRoomVideoClient",
    "DongchediVideoClient",
    "RutubeVideoClient",
]

PLATFORM_HINTS = (
    ("douyin.com", "抖音"),
    ("iesdouyin.com", "抖音"),
    ("tiktok.com", "TikTok"),
    ("bilibili.com", "哔哩哔哩"),
    ("b23.tv", "哔哩哔哩"),
    ("kuaishou.com", "快手"),
    ("kuaishouapp.com", "快手"),
    ("chenzhongtech.com", "快手"),
    ("kwai.com", "快手"),
    ("gifshow.com", "快手"),
    ("xiaohongshu.com", "小红书"),
    ("xhslink.com", "小红书"),
    ("weibo.com", "微博"),
    ("weibo.cn", "微博"),
    ("video.weibo.com", "微博"),
    ("youtube.com", "YouTube"),
    ("youtu.be", "YouTube"),
    ("instagram.com", "Instagram"),
    ("twitter.com", "X"),
    ("x.com", "X"),
    ("facebook.com", "Facebook"),
    ("fb.watch", "Facebook"),
    ("reddit.com", "Reddit"),
    ("redd.it", "Reddit"),
    ("vimeo.com", "Vimeo"),
)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
    "Mobile/15E148 Safari/604.1"
)
