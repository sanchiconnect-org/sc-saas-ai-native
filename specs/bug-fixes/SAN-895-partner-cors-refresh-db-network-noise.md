---
id: SAN-895
title: "Scheduled partner CORS cache refresh failed (122.176.150.231:3306) — local dev machines hitting the production DB without VPN/IP-whitelist access"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-895/sentry-sc-saas-backend-32-scheduled-partner-cors-cache-refresh-failed
sentry: [SC-SAAS-BACKEND-32, SC-SAAS-BACKEND-30, SC-SAAS-BACKEND-31, SC-SAAS-BACKEND-2Z]
repos: [backend]
commit: sc-saas-backend@<pending, branch ai_native_setup_aman>
created: 2026-09-24
updated: 2026-09-24
---

# SAN-895 (and SAN-896/897/898) — partner CORS cache refresh: local dev noise, not infra

## Root cause
Went through two incorrect framings before landing on the real one:
1. Original ticket framing: "external network/DNS/firewall problem reaching whatever this partner-CORS refresh's target host resolves to." Wrong — `PartnerCorsRegistryService.refreshCache()`'s only I/O is `PartnerEntity.createQueryBuilder(...).getMany()`, a query against this app's own MySQL connection (`DB_HOST`/`DB_PORT`, `database.config.ts`). There is no separate "partner CORS" service; the job is named for what it builds (CORS-allowed origins), not what it contacts.
2. My own first-pass fix: treated it as "an intermittent production DB-network blip" and downgraded the log to `.warn`. Also wrong on two counts — (a) this codebase's `SentryLoggerService` forwards both `.warn` and `.error` to Sentry (only `.debug`/`.log` are excluded), so the downgrade wouldn't have reduced Sentry noise at all; (b) it would have wrongly softened a genuine future production DB-outage on this same connection to `.warn`.
3. **Actual root cause, confirmed via the raw Sentry events**: all four issues (SC-SAAS-BACKEND-32/30/31/2Z) are tagged `environment: local`, from two developers' own machines (`server_name: sc-101`, `server_name: Mahima-Sharma-Mac-Book.local`), both on 2026-09-10 within the same ~30-minute window, zero production occurrences. `122.176.150.231:3306` is this tenant's real (production) database — there is no separate local DB for it to point at instead — so running the API locally without VPN/IP-whitelist access to that host produces exactly these connect/read errors. This is expected behavior for an unauthorized local machine hitting a properly firewalled production DB, not an application defect and not a production incident.

## Fix
- Reverted the `.warn` downgrade in `partner-cors-registry.service.ts` back to `.error` (a genuine production DB-reachability failure on this connection deserves to alert; the earlier downgrade attempt didn't actually address Sentry noise and would have misclassified severity).
- Added `isLocalPartnerCorsDbUnreachable` to `instrument.ts`'s `scrubEvent` — drops any event whose message includes `partner CORS cache refresh failed` **and** whose `environment === 'local'`, matching this file's existing precedent (`isMysqlPacketOrderWarning`, also local-dev-only noise). Scoping to `environment=local` (rather than dropping the message unconditionally) means a real production DB-reachability incident on this same connection still reaches Sentry and pages normally.

## Blast radius
`sc-saas-backend` only. No behavior change to `getCachedOrigins()`/`isAllowedOrigin()` or to production error visibility — only local-environment events matching this exact message are dropped before Sentry ingestion.

## Verification
`npx tsc --noEmit` clean. No test suite exists for either file; behavior verified by re-reading the `SentryLoggerService`/`CaptureConsole` levels config that motivated the correction, and by confirming the environment/server_name tags directly on the four Sentry events before writing the filter.

## Rollout
All four Sentry issues (SC-SAAS-BACKEND-32/30/31/2Z) marked resolved — confirmed dev-machine noise, not a production bug. If this message ever recurs with `environment: production`, it will NOT be filtered and should be treated as a real DB-reachability incident.

## Open questions
None.
