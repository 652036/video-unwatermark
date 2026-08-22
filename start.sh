#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Optional: ./start.sh --cookies /path/to/cookies.txt --cookies-from-browser chrome
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cookies)
      export UNWATERMARK_COOKIES="${2:-}"
      shift 2
      ;;
    --cookies-from-browser)
      export UNWATERMARK_COOKIES_FROM_BROWSER="${2:-}"
      shift 2
      ;;
    *)
      echo "[start] unknown arg: $1" >&2
      shift
      ;;
  esac
done

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m pip install videofetch || echo "[start] skip videofetch"
python -m pip install you-get || echo "[start] skip you-get"

python -c "from playwright.sync_api import sync_playwright" >/dev/null 2>&1 || python -m pip install playwright || echo "[start] skip playwright"

chrome_ok=0
if command -v google-chrome >/dev/null 2>&1 \
  || command -v google-chrome-stable >/dev/null 2>&1 \
  || command -v chromium >/dev/null 2>&1 \
  || command -v chromium-browser >/dev/null 2>&1; then
  chrome_ok=1
fi
# macOS Chrome.app (Playwright can also install its own Chromium)
if [[ -d "/Applications/Google Chrome.app" ]] || [[ -d "/Applications/Chromium.app" ]]; then
  chrome_ok=1
fi
if [[ "$chrome_ok" -eq 0 ]]; then
  python -m playwright install chromium || echo "[start] skip playwright chromium"
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[start] ffmpeg missing; trying package manager..."
  if [[ "$(uname -s)" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
    brew install ffmpeg || echo "[start] brew install ffmpeg failed (install manually)"
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg || true
  else
    echo "[start] install ffmpeg yourself (macOS: brew install ffmpeg; Debian/Ubuntu: sudo apt-get install ffmpeg)"
  fi
fi

if [[ -n "${UNWATERMARK_COOKIES:-}" ]]; then
  echo "[start] cookies file: ${UNWATERMARK_COOKIES}"
fi
if [[ -n "${UNWATERMARK_COOKIES_FROM_BROWSER:-}" ]]; then
  echo "[start] cookies_from_browser: ${UNWATERMARK_COOKIES_FROM_BROWSER}"
fi

# One source of truth: app.engines.lux picks the matching release asset.
echo "[start] ensuring lux for $(uname -s)/$(uname -m)..."
python -c "from app.engines.lux import ensure_lux, resolve_lux_asset, lux_bin_path; n,u=resolve_lux_asset(); print('[start] lux asset:', n); print('[start] lux bin:', lux_bin_path()); print('[start] lux ok' if ensure_lux() else '[start] lux missing (engine will skip)')" \
  || echo "[start] skip lux bootstrap"

export PYTHONUNBUFFERED=1
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
