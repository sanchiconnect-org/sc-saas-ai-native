---
id: SAN-1898
title: "booth-display chunk .find/.map of a section with no fields — same defect as SAN-1869"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1898
sentry: [SC-SAAS-FRONTEND-HB, SC-SAAS-FRONTEND-HC]
repos: [frontend]
commit: sc-saas-frontend@3914468c8 (branch ai_native_setup_vishali, pushed)
created: 2026-10-14
updated: 2026-10-14
---

## Root cause
HB/HC are the SAN-1869 (H0/H1) bug grouped under a different chunk name. The shared lazy chunk `booth-display…common-compone-958e22` bundles `public-profile-dynamic-single-form-view`. It's the same tenant (isgbb-bharatcares), the same release `bcf88383d` (2026-10-02) and the same frames (`isFieldVisible` → `s.fields.find`; subscribe `next` → `.map`). In `bcf88383d`, `isFieldVisible` used `s.fields.find(...)` unguarded. `c42bf95be` (SAN-1869) guards it, but that commit is not on `origin/main`, so production still runs the pre-fix code.

## Fix
- Root cause: none new. Deploying SAN-1869 resolves it.
- Hardening: `flatFieldValuesMapped` iterated `this.item.sections` → `s.fields` unguarded (same class). Now `(this.item?.sections || [])` / `(s?.fields || [])`. Also added the missing `;` after `const vals= {}` (needed so the leading `(` is not parsed as a call).

## Blast radius
`public-profile-dynamic-single-form-view.component.ts` only. When data is present the behaviour is identical. A section with no fields now contributes no values instead of throwing.

## Verification
`tsc --noEmit -p tsconfig.app.json` clean, eslint clean. No automated test added (no spec exists for this component). Not checked in a browser.

## Related
SAN-1869
