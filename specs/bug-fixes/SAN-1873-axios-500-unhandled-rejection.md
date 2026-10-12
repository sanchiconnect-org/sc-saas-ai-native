---
id: SAN-1873
title: "AxiosError 500 unhandled rejection still firing after SAN-988 (SC-SAAS-BACKEND-X)"
type: bug-fix
status: blocked
linear: https://linear.app/sanchiconnect/issue/SAN-1873
sentry: [SC-SAAS-BACKEND-X]
repos: [backend]
commit: none — blocked on the production redeploy of main
created: 2026-10-12
updated: 2026-10-12
---

# SAN-1873: AxiosError 500, call site still unknown

## Investigation
* 107 events, `onunhandledrejection`, no stack; the latest is 2026-10-07.
* The SAN-988 `runCronJob` wrapper (`ef9051b9`) has been in the running build since the 2026-10-02 main merge, so the cron callbacks are not the source.
* SAN-455 `attachAxiosRequest` (`fe33f96e`), which adds the axios_host/method/status tags, reached main only on 2026-10-11 (PR #2027) and is not deployed yet.
* Ruled out: `WhatsappService.sendMessages` catches its own error, and all direct axios calls are awaited.

## Plan
1. After deploy, read `axios_host` on the next event.
2. At the named call site, add `await` or `.catch()` with an attributed log line.

No code change now, because the call site is unknown.
