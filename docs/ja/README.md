# video-unwatermark

**公開**動画の共有文または URL を貼り付けると、サーバーが複数の抽出エンジンを並列で競わせ、なるべく透かしなし／原画の直リンクを返してダウンロードできます。

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

**公開 UGC のみ。** 会員制 / DRM プラットフォーム（Tencent Video、iQIYI、Youku、Mango TV、Netflix、Disney+、HBO、Prime Video、Spotify、Hulu など）はエンジン実行前に拒否されます。ログイン窃取、Cookie フィッシング、WeChat Channels の MITM は行いません。

## 機能

- Web UI：`http://127.0.0.1:8787` — 共有文や URL を貼り付け、プレビュー／ダウンロード
- マルチエンジン競合：最初に成功した抽出器が勝ち、他はキャンセル
- エンジン：`share-page`、`douyin-browser`（ヘッドレス Chrome）、`yt-dlp`、`videofetch`、`you-get`、`webparser`、`lux`
- 共有スローガンから最初の `http(s)` URL を抽出
- 任意のローカル Netscape Cookie / `--cookies-from-browser` は**最終手段**（代行取得なし）
- VIP / DRM ホストの明示的ブロック；WeChat Channels のログイン／MITM 拒否
- JSON API：parse、download、health、engines。OpenAPI は `/api/docs`

## クイックスタート

```bash
cd video-unwatermark
chmod +x start.sh
./start.sh
```

**http://127.0.0.1:8787** を開きます。

手動インストール：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# optional: pip install videofetch you-get
python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
```

`ffmpeg` が `PATH` にあること（yt-dlp の音声／映像結合用）。Debian/Ubuntu：

```bash
sudo apt-get install ffmpeg
```

`start.sh` は任意エンジン（`videofetch`、`you-get`、Playwright）の導入も試し、なければ Linux amd64 の `lux` を `bin/` に取得します。

## スクリーンショット

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

成功時は `ok`、`title`、`ext`、`filesize`、`thumbnail`、`extractor`、`platform`、`download_url`、`direct_url`、`preview_url`、`job` を返します。ゲスト遮断時は `{ok:false, needs_cookie:true, hint:"..."}` のことがあります。

タイムアウト：エンジンあたり約 25 秒、全体約 30 秒。Douyin/Kuaishou は最初に share-page + webparser + lux + `douyin-browser`（約 25 秒）を競わせ、全体最大約 95 秒。

## 対応サイトと制限

| Engine | Typical sites | Notes |
|---|---|---|
| **share-page** | Douyin, Kuaishou | Guest share-page HTML (`_ROUTER_DATA` / `__APOLLO_STATE__`); no login cookie |
| **douyin-browser** | Douyin | Headless Chrome; captures CDN `video_mp4` from `iesdouyin.com/share/video/{id}/` |
| **yt-dlp** | YouTube, Bilibili, TikTok, Instagram, X, Facebook, Reddit, Weibo, Vimeo, … | Follow [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) |
| **videofetch** | Douyin, Kuaishou, Xiaohongshu, Bilibili, … | Public-UGC clients only; VIP movie clients disabled |
| **you-get** | Some CN / social sites | Extra fallback parser |
| **webparser** | Douyin, Kuaishou | Keyless public JSON helpers (e.g. 17change, douyin.wtf hybrid) |
| **lux** | Douyin, Kuaishou | Local `bin/lux` binary; fallback only |

プラットフォーム API は頻繁に変わるため、失敗は普通です。ログイン壁の内容は `needs_cookie` になることがあります。

**既知の制限（正直に）：**

- **Douyin**: datacenter IPs often lack `play_addr` on share pages; yt-dlp may report `needs cookie`. Public hybrid parsers or `douyin-browser` may still succeed. Cookies are never stolen.
- **Kuaishou**: yt-dlp has no Kuaishou extractor. Existing `www.kuaishou.com/short-video/{id}` pages may parse via webparser; `v.kuaishou.com` shorts often expire; TLS EOF from some hosts is common.
- **Vimeo**: anonymous macos OAuth currently returns 401; use local `--cookies-from-browser` if you are logged in.
- **YouTube**: some IPs hit a bot wall (`Sign in to confirm you’re not a bot`); same optional local cookies apply.

検証メモ：[../test-results.md](../test-results.md)

## 任意 Cookie（最終手段）

一部サイト（特に Douyin / YouTube の bot wall）はデータセンターからの匿名アクセスを遮断します。本ツールは Cookie を**代行取得しません**。チャットに Cookie を貼らないでください。

**自分のマシン**で、**自分の** Netscape Cookie のみを渡します：

1. **CLI**

```bash
./start.sh --cookies /path/to/cookies.txt
./start.sh --cookies-from-browser chrome
```

   `cookies_from_browser` はそのマシンに入っているブラウザのみ。リモート VPS では無効です。

2. **環境変数**

```bash
export UNWATERMARK_COOKIES=/path/to/cookies.txt
export UNWATERMARK_COOKIES_FROM_BROWSER=chrome   # optional, local only
./start.sh
```

3. **Web / API** — ページの「Local Cookies」を開き、Netscape `cookies.txt` をアップロードするか `cookies_from_browser` を指定。JSON 形式の Cookie エクスポートは拒否されます。

アップロードは当該 parse/download のみに使われ、第三者チケット API には渡しません。

## アーキテクチャ

FastAPI が `static/` と JSON を提供します。`app/extract.py` が短縮 URL を展開し、ブロックホストを拒否したうえで段階的エンジン競合を実行します。最初の成功で短期ジョブを作り、`/api/download` がファイルを実体化します（必要なら ffmpeg 結合）。詳細：[../architecture.md](../architecture.md)。目次：[../README.md](../README.md)。

## コントリビューション

[../../CONTRIBUTING.md](../../CONTRIBUTING.md)。セキュリティ：[../../SECURITY.md](../../SECURITY.md)。変更履歴：[../../CHANGELOG.md](../../CHANGELOG.md)。

## ライセンス

[Apache License 2.0](../../LICENSE) — Copyright 2026 652036。サードパーティエンジンは各ライセンスのまま。[../../NOTICE](../../NOTICE) を参照。

## 免責事項

保存する権利のある公開コンテンツのみをダウンロードし、各プラットフォーム規約と現地法を守ってください。本プロジェクトは会員破解、DRM 復号、不正アクセスを**提供しません**。
