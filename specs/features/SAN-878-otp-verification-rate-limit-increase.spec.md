---
id: SAN-878
title: Increase OTP/verification rate limits from 3 to 10 req/60s
type: feature
status: approved
linear: https://linear.app/sanchiconnect/issue/SAN-878/backend-increase-otpverification-rate-limits-from-3-to-10-req60s
owner: aman.k@sanchiconnect.com
repos: [backend]
contracts:
  api: []
  flags: []
  events: []
tenant_scoped: false
depends_on: []
created: 2026-09-21
---

# Increase OTP/verification rate limits from 3 to 10 req/60s

## Problem
Five OTP/verification-code endpoints in `sc-saas-backend`'s `auth.controller.ts` are rate-limited to `points: 3` per `duration: 60` seconds. A mistyped code, or a slow-arriving SMS/email prompting a manual retry, burns through that ceiling fast and locks the user out with a 429. Raise the ceiling to 10/60s.

## Acceptance criteria
- [ ] Every `@RateLimit()` decorator on the 5 endpoints below reads `points: 10` (was `3`); `duration: 60` unchanged.
- [ ] No other decorator option, DTO, route path, or response shape changes.

## Per-repo plan

### backend
- `src/modules/auth/auth.controller.ts` — bump `points: 3` → `points: 10` on:
  - `POST mobile/login/verify` (`OTP_VERIFY`, ~line 112-118)
  - `GET verify/mobile/:mobileNumber` (`MOBILE_VERIFY`, ~line 227-233)
  - `GET verify/email/:email` (`EMAIL_VERIFY`, ~line 260-266)
  - `POST verify/email` (`EMAIL_VERIFY`, ~line 333-339)
  - `POST verify/email-token` (`EMAIL_TOKEN_VERIFY`, ~line 362-368)
- `src/modules/auth/module.spec.md` — update the rate-limit note under "Internal model" to reflect the new ceiling.

## Contracts & invariants
- **API:** no route, DTO, or response-shape change — purely a rate-limiter threshold. `/audit-contract` should report zero drift.
- **Flags:** none touched.
- **Events:** none touched.
- **Invariants at risk:** none. Doesn't touch the JWT/auth model itself (workspace invariant #4) — only how many verification attempts are allowed before a 429.

## Test plan
- backend: no automated test added, per explicit instruction. Verified via `tsc --noEmit`, `eslint`, and a manual read of the decorator values before/after.
- cross-repo: none — frontend/admin callers are unaffected by a looser rate limit.

## Rollout
Single-repo, single-deploy change. No flag gating needed.

## Out of scope
- `verifications.controller.ts`'s `POST /send` / `POST /verify` OTP endpoints — already at `points: 5`, not 3; not part of this ticket's literal "3 → 10" ask (flagged on the Linear issue for a separate decision, not decided here).
- `send/whatsapp` OTP (`verifications.controller.ts`) — its `RateLimiterGuard` is commented out entirely (pre-existing dead rate limit); unrelated, not touched here.
- `GET verify/partner-abbreviation/:abbreviation` — already at `points: 10`; no change needed.

## Open questions
(none — scope is fully evidence-checked against current source; nothing pending)
