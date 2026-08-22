# Security Policy

## Supported versions

Report issues against the latest `main` branch.

## Reporting a vulnerability

Open a GitHub issue titled `[security] …` with:

- Affected endpoint or engine
- Impact summary
- Reproduction steps that do **not** require sharing real cookies or session tokens

If the report must stay private, describe the issue at a high level in the ticket and ask maintainers for a private channel.

## Out of scope

- Requests to crack VIP / DRM / membership platforms
- Asking us to harvest or proxy someone else’s cookies
- WeChat Channels login/MITM tooling
- Social-engineering or phishing recipes

This project will not add those capabilities.

## Cookie handling

Optional Netscape cookies and `--cookies-from-browser` are **user-supplied, local last resorts**. The service never fetches login state from third-party sites on your behalf. Do not paste cookie files into public issues.
