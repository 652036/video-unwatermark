# video-unwatermark

> ملاحظة اتجاه النص: المحتوى العربي أدناه يُعرض بشكل طبيعي في Markdown؛ قد تحتاج واجهة GitHub إلى تفعيل RTL في المتصفح.

الصق نص مشاركة أو رابط فيديو **عام**. يشغّل الخادم عدة محركات استخراج بالتوازي ويعيد رابطًا مباشرًا (يفضَّل بلا علامة مائية) لتنزيل الملف الأصلي.

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

**محتوى UGC العام فقط.** تُرفض منصات الاشتراك / DRM (Tencent Video وiQIYI وYouku وMango TV وNetflix وDisney+ وHBO وPrime Video وSpotify وHulu وما شابه) قبل تشغيل أي مستخرج. هذا المشروع لا يسرق جلسات الدخول ولا يصطاد ملفات تعريف الارتباط ولا ينفّذ MITM على WeChat Channels.

## الميزات

- واجهة ويب على `http://127.0.0.1:8787` — لصق النص/الرابط، معاينة، تنزيل
- سباق متعدد المحركات: أول نجاح يفوز؛ تُلغى البقية
- المحركات: `share-page`، `douyin-browser` (Chrome بلا واجهة)، `yt-dlp`، `videofetch`، `you-get`، `webparser`، `lux`
- يستخرج أول رابط `http(s)` من شعارات المشاركة
- ملفات Netscape cookies محلية اختيارية / `--cookies-from-browser` كـ**حل أخير** (لا تُجلب نيابة عنك)
- قائمة حظر صريحة لـ VIP / DRM؛ رفض التقاط تسجيل الدخول/MITM لـ WeChat Channels
- واجهة JSON: parse وdownload وhealth وengines؛ OpenAPI على `/api/docs`

## البدء السريع

```bash
cd video-unwatermark
chmod +x start.sh
./start.sh
```

Windows: `.\start.ps1` (أو `start.bat`).

افتح **http://127.0.0.1:8787**.

تثبيت يدوي:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# optional: pip install videofetch you-get
python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
```

يجب أن يكون `ffmpeg` في `PATH` (دمج الصوت/الفيديو عبر yt-dlp):

```bash
# macOS
brew install ffmpeg
# Debian / Ubuntu
sudo apt-get install ffmpeg
# Windows
winget install --id Gyan.FFmpeg -e
```

يحاول `start.sh` (macOS/Linux) أو `start.ps1` (Windows) أيضًا تثبيت المحركات الاختيارية (`videofetch` و`you-get` وPlaywright) وتنزيل `lux` المناسب لنظامك/معالجك إلى `bin/` عند الحاجة.

## واجهة البرمجة API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/parse` | Body `{"url":"..."}` or multipart (`url`, optional `cookies_file`, `cookies_from_browser`) |
| `GET` | `/api/download?job=...` | Attachment download for a parse job |
| `GET` | `/api/preview?job=...` | Stream preview for a job |
| `GET` | `/api/health` | Engine + ffmpeg status; cookie flags only say *configured*, never contents |
| `GET` | `/api/engines` | Engine list |
| `GET` | `/api/docs` | OpenAPI UI |

تتضمن الاستجابة الناجحة `ok` و`title` و`ext` و`filesize` و`thumbnail` و`extractor` و`platform` و`download_url` و`direct_url` و`preview_url` و`job`. عند حظر الزائر قد تُرجع `{ok:false, needs_cookie:true, hint:"..."}`.

المهلات: ~25 ثانية لكل محرك، ~30 ثانية إجمالًا؛ Douyin/Kuaishou يتسابقان أولًا عبر share-page + webparser + lux + `douyin-browser` (~25 ث)، وحتى ~95 ث إجمالًا.

## المواقع المدعومة والحدود

| Engine | Typical sites | Notes |
|---|---|---|
| **share-page** | Douyin, Kuaishou | Guest share-page HTML (`_ROUTER_DATA` / `__APOLLO_STATE__`); no login cookie |
| **douyin-browser** | Douyin | Headless Chrome; captures CDN `video_mp4` from `iesdouyin.com/share/video/{id}/` |
| **yt-dlp** | YouTube, Bilibili, TikTok, Instagram, X, Facebook, Reddit, Weibo, Vimeo, … | Follow [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) |
| **videofetch** | Douyin, Kuaishou, Xiaohongshu, Bilibili, … | Public-UGC clients only; VIP movie clients disabled |
| **you-get** | Some CN / social sites | Extra fallback parser |
| **webparser** | Douyin, Kuaishou | Keyless public JSON helpers (e.g. 17change, douyin.wtf hybrid) |
| **lux** | Douyin, Kuaishou | Local `bin/lux` binary; fallback only |

تتغيّر واجهات المنصات كثيرًا؛ الفشل أمر طبيعي. المحتوى خلف تسجيل الدخول قد يعيد `needs_cookie`.

**قيود معروفة (بصدق):**

- **Douyin**: datacenter IPs often lack `play_addr` on share pages; yt-dlp may report `needs cookie`. Public hybrid parsers or `douyin-browser` may still succeed. Cookies are never stolen.
- **Kuaishou**: yt-dlp has no Kuaishou extractor. Existing `www.kuaishou.com/short-video/{id}` pages may parse via webparser; `v.kuaishou.com` shorts often expire; TLS EOF from some hosts is common.
- **Vimeo**: anonymous macos OAuth currently returns 401; use local `--cookies-from-browser` if you are logged in.
- **YouTube**: some IPs hit a bot wall (`Sign in to confirm you’re not a bot`); same optional local cookies apply.

## ملفات تعريف الارتباط الاختيارية (حل أخير)

بعض المواقع (خاصة Douyin / جدار بوتات YouTube) تحجب عناوين IP لمراكز البيانات. هذه الأداة **لن** تجلب cookies نيابة عنك. **لا** تلصق cookies في المحادثات.

على **جهازك**، قدّم **ملفاتك** بصيغة Netscape فقط:

1. **سطر الأوامر**

```bash
./start.sh --cookies /path/to/cookies.txt
./start.sh --cookies-from-browser chrome
```

   يقرأ `cookies_from_browser` المتصفحات المثبّتة على **ذلك** الجهاز فقط. عديم الفائدة على VPS بعيد بلا ملفك الشخصي.

2. **متغيرات البيئة**

```bash
export UNWATERMARK_COOKIES=/path/to/cookies.txt
export UNWATERMARK_COOKIES_FROM_BROWSER=chrome   # optional, local only
./start.sh
```

3. **الويب / API** — افتح «Local Cookies»، ارفع `cookies.txt` بصيغة Netscape أو اختر `cookies_from_browser`. تُرفض تصديرات JSON.

الملفات المرفوعة تُستخدم فقط في عملية التحليل/التنزيل الحالية؛ لا تُبادل بتذاكر طرف ثالث.

## البنية المعمارية

يقدّم FastAPI ملفات `static/` ومسارات JSON. يوسّع `app/extract.py` الروابط القصيرة، يرفض المضيفين المحظورين، ثم يشغّل سباقات مرحلية. أول `ok` ينشئ مهمة قصيرة؛ `/api/download` يُخرج الملف (مع دمج ffmpeg عند الحاجة). التفاصيل: [../architecture.md](../architecture.md). الفهرس: [../README.md](../README.md).

## المساهمة

راجع [../../CONTRIBUTING.md](../../CONTRIBUTING.md). الأمن: [../../SECURITY.md](../../SECURITY.md). سجل التغييرات: [../../CHANGELOG.md](../../CHANGELOG.md).

## الرخصة

[Apache License 2.0](../../LICENSE) — Copyright 2026 652036. تبقى محركات الطرف الثالث تحت رخصها؛ انظر [../../NOTICE](../../NOTICE).

## إخلاء المسؤولية

نزّل فقط المحتوى العام الذي يحق لك حفظه. احترم شروط كل منصة والقانون المحلي. هذا المشروع **لا** يوفّر كسر الاشتراكات ولا فك DRM ولا وصولًا غير مصرّح به.
