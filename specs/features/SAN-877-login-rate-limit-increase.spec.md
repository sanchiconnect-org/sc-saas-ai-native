---
id: SAN-877
title: Increase login rate limit from 3 to 10 req/60s
type: feature
status: approved
linear: https://linear.app/sanchiconnect/issue/SAN-877/backend-increase-login-rate-limit-from-3-to-10-req60s
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

# Increase login rate limit from 3 to 10 req/60s

## Problem
`POST mobile/login` in `sc-saas-backend`'s `auth.controller.ts` is rate-limited to `points: 3` per `duration: 60` seconds. A user who mistypes their mobile number or password more than twice within a minute gets locked out with a 429 and has to wait out the window. Raise the ceiling to 10/60s.

## Acceptance criteria
- [ ] The `LOGIN`-key-prefixed `@RateLimit()` decorator on `POST mobile/login` reads `points: 10` (was `3`); `duration: 60` unchanged.
- [ ] No other decorator option, DTO, route path, or response shape changes.

## Per-repo plan

### backend
- `src/modules/auth/auth.controller.ts` — bump `points: 3` → `points: 10` on `POST mobile/login` (~line 82-88).
- `src/modules/auth/module.spec.md` — update the rate-limit note under "Internal model" to reflect the new ceiling.

## Contracts & invariants
- **API:** no route, DTO, or response-shape change — purely a rate-limiter threshold. `/audit-contract` should report zero drift.
- **Flags:** none touched.
- **Events:** none touched.
- **Invariants at risk:** none. Doesn't touch the JWT/auth model itself (workspace invariant #4) — only how many login attempts are allowed before a 429.

## Test plan
- backend: no automated test added, per explicit instruction. Verified via `tsc --noEmit`, `eslint`, and a manual read of the decorator value before/after.
- cross-repo: none — frontend/admin callers are unaffected by a looser rate limit.

## Rollout
Single-repo, single-deploy change. No flag gating needed.

## Out of scope
- `mobile/login/verify` (OTP verification step of login) is a separate `OTP_VERIFY`-prefixed decorator, covered under SAN-878, not this issue.

## Open questions
(none — scope is fully evidence-checked against current source; nothing pending)
