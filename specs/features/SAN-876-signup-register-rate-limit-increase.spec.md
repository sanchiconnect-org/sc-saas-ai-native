---
id: SAN-876
title: Increase signup/register rate limits from 3 to 10 req/60s
type: feature
status: approved
linear: https://linear.app/sanchiconnect/issue/SAN-876/backend-increase-signupregister-rate-limits-from-3-to-10-req60s
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

# Increase signup/register rate limits from 3 to 10 req/60s

## Problem
Every registration endpoint in `sc-saas-backend`'s `auth.controller.ts` is rate-limited to `points: 3` per `duration: 60` seconds (`nestjs-rate-limiter`'s `RateLimiterGuard` + `@RateLimit()`). 3 requests/minute is tight enough that a real applicant can get locked out after two or three form-validation retries (a typo in mobile number/email, a slow OTP, a rejected password), producing a 429 with no useful recovery except waiting out the window. Raise the ceiling to 10/60s — generous enough for retries, still bounded against abuse.

## Acceptance criteria
- [ ] Every `REGISTER`-key-prefixed `@RateLimit()` decorator in `auth.controller.ts` reads `points: 10` (was `3`); `duration: 60` unchanged.
- [ ] No other decorator option (`keyPrefix`, `errorMessage`) changes.
- [ ] No DTO, route path, response shape, or guard order changes — this is a threshold-only change.

## Per-repo plan

### backend
- `src/modules/auth/auth.controller.ts` — bump `points: 3` → `points: 10` on the `REGISTER`-prefixed decorators:
  - `POST register` (~line 150-156)
  - `POST event/register` (~line 192-198)
  - `POST register/other` (~line 397-403)
  - `POST register/job-seeker` (~line 437-443)
  - `POST register/startup` (~line 475-481)
- `src/modules/auth/module.spec.md` — update the rate-limit note under "Internal model" to reflect the new ceiling.

## Contracts & invariants
- **API:** no route, DTO, or response-shape change — purely a rate-limiter threshold. `/audit-contract` should report zero drift.
- **Flags:** none touched.
- **Events:** none touched.
- **Invariants at risk:** none. This doesn't touch the JWT/auth model itself (workspace invariant #4) — it only changes how many attempts are allowed before a 429, not how authentication works.

## Test plan
- backend: no automated test added, per explicit instruction. Verified via `tsc --noEmit`, `eslint`, and a manual read of the decorator values before/after.
- cross-repo: none — frontend/admin callers are unaffected by a looser rate limit (they only observe fewer 429s, no contract change to react to).

## Rollout
Single-repo, single-deploy change. No flag gating needed (a wider rate limit is safe to ship directly — it only loosens an existing protection, never removes it).

## Out of scope
- `verifications.controller.ts`'s `POST /send` / `POST /verify` OTP endpoints — already at `points: 5`, not 3; not part of this ticket's literal "3 → 10" ask (flagged on the Linear issue for a separate decision).
- The commented-out `RateLimiterGuard` on `send/whatsapp` OTP — pre-existing, unrelated gap, not touched here.

## Open questions
(none — scope is fully evidence-checked against current source; nothing pending)
