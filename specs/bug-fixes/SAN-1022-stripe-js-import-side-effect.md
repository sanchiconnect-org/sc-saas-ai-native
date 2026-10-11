---
id: SAN-1022
title: "Failed to load Stripe.js on every dynamic-form page"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1022
sentry: [SC-SAAS-FRONTEND-2C]
repos: [frontend]
commit: sc-saas-frontend@<uncommitted — awaiting Mahima's verification; working branch ai_native_setup_mahima>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1022

## Root cause (CODE_ERROR)
payment-gateways.component.ts and payment/checkout/checkout.component.ts import the main `@stripe/stripe-js` entry, which injects Stripe.js as an import side effect on every dynamic-forms page; blocked loads report the error. SAN-933 only guarded loadStripe().

## Fix
`import { loadStripe } from '@stripe/stripe-js/pure'` + `import type { Stripe }` in both files (pure entry exists in v7.0.0).

## Existing-flow check
No global window.Stripe usage anywhere; checkout still loads Stripe via loadStripe().

## Verification
`npx tsc -p tsconfig.app.json --noEmit` clean (whole app). No automated regression test yet — proposed, awaiting approval (workspace step 6 blocked, no guardian skill). Contract check: frontend-only, no controller/DTO/flag touched → /audit-contract, /trace-flag, /check-isolation N/A.
