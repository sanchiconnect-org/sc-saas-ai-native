---
id: SAN-832
title: "connections-v3 nav crashes reading 'pendingConnectionCount' before notification counts load"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-832
sentry:
  - SC-SAAS-FRONTEND-DR
repos: [frontend]
commit: sc-saas-frontend@e3a56146 (branch ai_native_setup_vishali, committed — not yet pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-832 — connections-v3 notificationsCount race

## Root cause
`connections-v3.component.html:46-47`:
```html
<ng-container *ngIf="notificationsCount[link.countKey]">
  ({{notificationsCount[link.countKey]}})
</ng-container>
```
`notificationsCount` is undefined until the `getNotificationsCount` store selector emits; both the `*ngIf` and interpolation index into it with no optional chaining, throwing `TypeError: Cannot read properties of undefined (reading 'pendingConnectionCount')` during the initial load window.

A similar bug in `service-provider-dashboard` was already fixed this way via commit `fa4471fd`, but this file wasn't included in that fix.

## Fix
`notificationsCount?.[link.countKey]` in both places. Once the selector emits, indexing behaves exactly as before; during the initial undefined window the nav badge now renders nothing instead of throwing.

No API/DTO/flag/tenant-scoping impact — template-only optional-chaining addition.

## Blast radius
`sc-saas-frontend`'s connections-v3 page nav badges only.

## Verification
Full `ng build --configuration development` (AOT) — exit code 0, no errors on this file (template-only change, `tsc` doesn't cover it but AOT compilation does). No automated test suite exists for this repo yet — manual repro (load the connections page, confirm nav badges render without a console error before count data arrives) is the substitute verification, still to be done by hand before commit.

## Related
Same pattern/fix as the already-shipped `service-provider-dashboard` fix (`fa4471fd`) — this ticket ports it to the one file that was missed.
