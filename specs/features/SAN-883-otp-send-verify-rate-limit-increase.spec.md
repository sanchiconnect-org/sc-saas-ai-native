---
id: SAN-883
title: Increase OTP send/verify rate limits from 5 to 10 req/60s
type: feature
status: approved
linear: https://linear.app/sanchiconnect/issue/SAN-883/backend-increase-otp-sendverify-rate-limits-from-5-to-10-req60s
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

# Increase OTP send/verify rate limits from 5 to 10 req/60s

## Problem
`verifications.controller.ts`'s `POST /send` and `POST /verify` OTP endpoints are rate-limited to `points: 5` per `duration: 60` seconds. Bring them to `points: 10` for consistency with the rest of this milestone (SAN-876/877/878, all raised to 10). Explicitly confirmed by the requester after being flagged as out-of-scope on SAN-878.

## Acceptance criteria
- [ ] `POST /send` (`SEND_OTP`) and `POST /verify` (`VERIFY_OTP`) both read `points: 10` (was `5`); `duration: 60` unchanged.
- [ ] `POST /send/whatsapp`'s dead (commented-out) `RateLimiterGuard` is left untouched — not part of this change.
- [ ] No DTO, route path, or response shape changes.

## Per-repo plan

### backend
- `src/modules/verifications/verifications.controller.ts` — bump `points: 5` → `points: 10` on:
  - `POST /send` (~line 49-56)
  - `POST /verify` (~line 70-77)
- `src/modules/verifications/module.spec.md` — update the documented rate limit (currently states "5/60s") to 10/60s.

## Contracts & invariants
- **API:** no route, DTO, or response-shape change — purely a rate-limiter threshold. `/audit-contract` should report zero drift (these are unauthenticated public endpoints per the module's own spec; no admin consumer expected).
- **Flags:** none touched.
- **Events:** none touched.
- **Invariants at risk:** none.

## Test plan
- backend: no automated test added, per explicit instruction. Verified via `tsc --noEmit`, `eslint`, and a manual read of the decorator values before/after — confirmed `sendWhatsappOTP`'s metadata (`points: 6`, guard still commented out) was left untouched.
- cross-repo: none — looser rate limit doesn't affect any consumer's request/response handling.

## Rollout
Single-repo, single-deploy change. No flag gating needed.

## Out of scope
- `POST /send/whatsapp`'s commented-out `@UseGuards(RateLimiterGuard)` — enabling it would add enforcement where none exists today, a different kind of change than raising an existing threshold. Not decided here.

## Open questions
(none — scope is fully evidence-checked against current source; nothing pending)
