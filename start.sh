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
if ! command -v google-chrome >/dev/null 2>&1 && ! command -v google-chrome-stable >/dev/null 2>&1 && ! command -v chromium >/dev/null 2>&1; then
  python -m playwright install chromium || echo "[start] skip playwright chromium"
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[start] ffmpeg missing; trying apt..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg || true
  fi
fi

if [[ -n "${UNWATERMARK_COOKIES:-}" ]]; then
  echo "[start] cookies file: ${UNWATERMARK_COOKIES}"
fi
if [[ -n "${UNWATERMARK_COOKIES_FROM_BROWSER:-}" ]]; then
  echo "[start] cookies_from_browser: ${UNWATERMARK_COOKIES_FROM_BROWSER}"
fi

if [[ ! -x "$ROOT/bin/lux" ]]; then
  echo "[start] fetching lux Linux amd64 release asset..."
  mkdir -p "$ROOT/bin"
  if curl -fsSL -o /tmp/lux.tgz "https://github.com/iawia002/lux/releases/download/v0.24.1/lux_0.24.1_Linux_x86_64.tar.gz"; then
    tar -xzf /tmp/lux.tgz -C "$ROOT/bin" lux && chmod +x "$ROOT/bin/lux" || echo "[start] skip lux extract"
    rm -f /tmp/lux.tgz
  else
    echo "[start] skip lux download"
  fi
fi

export PYTHONUNBUFFERED=1
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
