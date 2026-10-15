# Sentry sweep — 2026-10-15

* **Scope:** all Sentry projects, `is:unresolved`, last 14 days. 28 issues.
* **Filed:** SAN-1922 to SAN-1932 in the Linear **Production Defects** project, milestone M5, all assigned to Vishali.
* **Code changes:** pushed to `ai_native_setup_vishali`: backend `688f5870` (SAN-1923), `4843fd2c` (SAN-1931); frontend `5548dff24` (SAN-1929), `0a09edb32` (SAN-1930); admin `f7020899` (SAN-1922). Not yet on main, so not deployed.

## Tickets

| Ticket | Repo | Sentry | Outcome |
|---|---|---|---|
| [SAN-1922](SAN-1922-admin-tenant-db-access-denied-1045.md) | admin | ADMIN-14 | Ops: aktu tenant DB password mismatch. Code: 503 page instead of a fatal error. |
| [SAN-1923](SAN-1923-forms-out-of-sort-memory.md) | backend | BACKEND-5S, FRONTEND-2W | Forms queries now sort in Node, not MySQL. The 2W 504 is likely the 10-14 DB degradation. |
| [SAN-1924](SAN-1924-tenants-ecosystem-partners-unknownvalue-stale-build.md) | tenants | TENANTS-2 | Already fixed by SAN-1014; the events came from a stale build. No change. |
| [SAN-1925](SAN-1925-frontend-fixes-not-deployed-stale-pwa.md) | frontend | H0, H1, 2J, 17 | Deploy lag and stale PWA builds. Needs promote + redeploy. |
| [SAN-1926](SAN-1926-backend-fixes-not-on-main.md) | backend | 3M, 5Q, 9, X | Fixes not on main. Needs promote + redeploy. |
| [SAN-1927](SAN-1927-analyzer-thesis-timeout.md) | ai-analyzer | ANALYZER-4 | Not started (repo not cloned). |
| [SAN-1928](SAN-1928-something-went-wrong-is-frontend-fallback.md) | backend | FRONTEND-F2, G0 | Frontend fallback text for network failures. No defect. |
| [SAN-1929](SAN-1929-clipboard-writetext-unhandled.md) | frontend | FRONTEND-HG | Shared clipboard helper used at 6 sites. |
| [SAN-1930](SAN-1930-network-0-504-and-expected-faults.md) | frontend | 1, H3, HE, HF, 49, EX, 9A, 4A | Public-events and uploadLogo error handling. The rest are already handled or fixed. |
| [SAN-1931](SAN-1931-saas-settings-502-on-cache-clear.md) | backend | BACKEND-1H | Cache-clear keeps the last good settings when the cockpit returns 502. |
| [SAN-1932](SAN-1932-tenants-admin-too-many-connections-recurrence.md) | tenants-admin | TENANTS-ADMIN-4 | Infra connection exhaustion. Recommendations only. |

## Not ticketed
* **BACKEND-4Q / 5N:** already open as SAN-1871 (Todo, Aman).
* **FRONTEND-17 (lightGallery):** noise per the board policy; it's in SAN-1925 because the fix is on main.

## Cross-cutting
* **Deploy lag again.** Frontend `ai_native_setup_vishali` is 79 commits ahead of `origin/main`, and four backend fixes are off main. Promoting and redeploying is the highest-value action.
* **DB pressure on 2026-10-11 to 10-14** links BACKEND-5S, FRONTEND-2W/F2/G0/H3/HE/HF and TENANTS-ADMIN-4. Check the RDS metrics for that window.
* **Possible secret exposure:** PHP Sentry stack frames (ADMIN-14 / ADMIN-5) may contain the tenant DB password. A Security ticket is pending a decision.
