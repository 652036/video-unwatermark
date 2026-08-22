# Contributing

Thanks for helping improve **video-unwatermark**.

## Scope

- This project parses **public UGC** only.
- Do **not** send PRs that unlock VIP/DRM, steal logins, phish cookies, or MITM WeChat Channels.
- Do **not** invent engines or claim sites work without a real parse success.

## Development

```bash
./start.sh
# or
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8787
```

Useful endpoints: `/`, `/api/health`, `/api/engines`, `/api/docs`.

## Pull requests

1. Fork and branch from `main`.
2. Keep changes focused; prefer small PRs.
3. Update docs if behavior changes (especially README limitations).
4. Do not commit `.venv/`, `downloads/`, `bin/lux`, cookies, or smoke JSON dumps.
5. Fill the PR template.

## Issues

Use the bug / feature templates. Include the platform URL pattern (redact private data), engine from `/api/health`, and whether cookies were used. Requests for VIP cracking will be closed.

## License

By contributing, you agree your work is licensed under Apache-2.0 (Copyright 2026 652036).
