# sc-saas-backend Sentry project — triage of all 33 unresolved issues (2026-10-06)

Source: Sentry project `sc-saas-backend`, `is:unresolved`, 90 days. Environment split: **14 issues have production events; 19 have none** (local/test only).
Assignee for every item that needed work: Aman kabra.

## A. Production issues (14)

| Sentry | Disposition | Evidence |
|---|---|---|
| BACKEND-4B, 4R | Resolved | Pending-connection-reminder template malformed. Repaired at startup by SAN-1354 (`64a44589`, repo + admin seed SAN-1355 `be62c6ab`); one failure per run by SAN-189 (`f5bb515f`). 16 siblings were resolved earlier. |
| BACKEND-3J | Resolved | `moment('2026:09:25')` in `admin-actions.service.sendEventOneToOneLiveEmail`. Fixed by SAN-1008 (`c94c4d12`, 2026-09-25 16:49); all 4 events are from that morning, before the fix. |
| BACKEND-4M, 4T | Resolved | `stopped early -- TooManyRequestsException`. SAN-1353 re-classified a throttle as a pause; the message is no longer emitted. |
| BACKEND-4X | Fixed here: SAN-1663 | A throttle pause was a warning (forwarded to Sentry) on every run; now quiet unless it persists. |
| BACKEND-3N, 34, 3P | Fixed here: SAN-1664 | Duplicate-label diagnostic now warns once per form/label. Remedy for the data is renaming the fields on forms 20 and 1. |
| BACKEND-1T | Resolved (inference) | `connect ECONNREFUSED 15.206.245.89:443` as an unhandled rejection. SAN-988 (`ef9051b9`, 2026-09-24) wraps every cron callback in `.catch`; it reached `main` 2026-09-25 13:55 and the last 1T event is 15:14 the same day. No call site is provable, confidence medium; if it recurs the wrapper logs `Cron job "<name>" failed` with the real stack. |
| BACKEND-3M | Open | `Unknown column 'NaN' in 'field list'` (INSERT/UPDATE with a numeric NaN). Production runs a build from before `d254dc94` (2026-10-05), which names the failing statement (`failedQuery`, `failed_table`) and guards 0/0 percentages. Eight aggregate-percentage sites were checked and are not reachable with a zero total (the corporate criteria list is never empty). No guess-fix. Needs the next event after deploy. |
| BACKEND-4F | Open | `Column 'profile_type' cannot be null`. Same diagnostic as 3M; SAN-1152 investigation was inconclusive. |
| BACKEND-X | Open | `AxiosError: ... status code 500`. `fe33f96e` (SAN-455) now tags host/method/status; needs a post-deploy event. |
| BACKEND-9 | Open | S3 `SignatureDoesNotMatch`. S3 client config is correct (`signatureVersion v4`, path-style, endpoint from config); credentials, endpoint or clock skew in the production task definition. Infra. |
| BACKEND-1H | Open | `ETIMEDOUT` fetching SaaS settings from the cockpit, last seen 28 days ago; connectivity, not code. |

## B. No production events — local or test noise (19)

Not production defects: none of these has a single `environment: production` event.

- **Another project reporting into this one (SanchiJawab, a separate Python/FastAPI app):** BACKEND-4S, 4Y, 4W, 51, 4Z, 4V. Platform `python`, paths such as `/v1/auth/signup` and `/v1/workspaces/{id}/orders`, `WinError`, pytest runs (`pytest -q`, recipient `pytest_…@example.com`), `server_name: AmanK`. That app's DSN points at this Sentry project; fix it in that repo (use its own DSN, and do not initialise Sentry under pytest).
- **Local Docker / dev credentials:** BACKEND-4K, 4N (SMTP 535 invalid login), 4J, 4G, 4P (SES stats with a dev IAM user), 3K (bulk insert, over-length LinkedIn URL at row 165, local only).
- **External dev service:** BACKEND-2C, 4H, 33 (`dev-api.videopitchrecorder.com` create-session 404 / its DB refusing connections).
- **Node/process noise:** BACKEND-2X (punycode deprecation warning from a dependency), 2W (write after end), 2Y (EADDRINUSE: a second local instance).
- BACKEND-4T is listed in section A (same cause as 4M).

## Verification
Production vs local split from `environment:production` / `environment:local` searches; event details read for 4Y, 3K, 3J, 4K, 3M, 1T. Commit evidence from `git log -S`.
