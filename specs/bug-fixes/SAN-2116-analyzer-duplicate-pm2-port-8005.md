---
id: SAN-2116
title: "uvicorn fails to bind 127.0.0.1:8005 'address already in use' — duplicate PM2 entry on the dev host"
type: bug-fix
status: todo (assigned to Aman kabra)
linear: https://linear.app/sanchiconnect/issue/SAN-2116
sentry: [AI-STARTUPS-ANALYZER-8]
repos: [ai-analyzer]
related: []
commit: none — infra fix on the host
created: 2026-10-28
updated: 2026-10-28
---

# SAN-2116: two PM2 apps want port 8005

## Investigation
* AI-8: 98 events between 10-26 11:50 and 10-27 04:42 UTC, escalating. Host `sanchiconnect`, environment `local`.
* `api/ecosystem.config.js` (added in `53c7b8f`, the OOM fix) defines PM2 app `ai-analyzer-dev-api` as `./venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8005` with `autorestart`. Its header says it replaces the old inline `pm2 start "..."` string.
* The failing argv in Sentry is `/var/www/ai-startups-analyzer/api/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8005`. That is the `venv/bin/uvicorn` binary, i.e. the **old inline PM2 entry**, not the ecosystem one.
* Both are registered: one holds 8005, and the other crash-loops on bind under autorestart.

## Fix (host, not git)
`pm2 ls`, then `pm2 delete` the old `venv/bin/uvicorn` entry, `pm2 restart ai-analyzer-dev-api`, and `pm2 save`. The Jenkins dev job must use `pm2 startOrReload ecosystem.config.js`, not the old inline start. Also set `SENTRY_ENVIRONMENT=development` on the host.

## Open
Needs dev-server / Jenkins access (Aman).
