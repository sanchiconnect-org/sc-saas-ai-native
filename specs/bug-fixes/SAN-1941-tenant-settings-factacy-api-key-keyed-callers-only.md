# SAN-1941 — Public tenant-settings still returns factacy_api_key

Linear: https://linear.app/sanchiconnect/issue/SAN-1941 · Repo: `sanchiconnect-saas-tenants` · Priority: High · Assignee: Sandeep
Classification: **CODE_ERROR** (the key itself still needs rotating: ENV/ops, see below)

## Problem
`GET {cockpit}/api/v1/public/global/tenant-settings/{hostname}` returns `data.settings.factacy_api_key` with a live value to an anonymous caller (found by sc-saas-e2e SAN-1609 on the dev cockpit; its test is `test.fail()`).

## Root cause
`getTenantSettings()` copies every `global_settings` row into the response except the codes in `COCKPIT_ONLY_GLOBAL_SETTINGS`, which held only `currency_api_key` (440d15d). `factacy_api_key` is a seeded row (SAN-1914 made the seed read `FACTACY_API_KEY` from the env), so it was delivered. The route's `CockpitCallerKeyGuard` (SAN-44 S7) runs in `log` mode by default: a call without the key is still answered.

## Key finding (changes the fix)
The ticket suggested simply stopping the key. But `sc-saas-backend` reads it from this payload: `FactacyService.onApplicationBootstrap()` sets `x-api-key: saasSettings[SaaSSettingKey.FACTACY_API_KEY]` for `GET api/v1/factacy/ai-news` (flag `factacy_enabled`). Withholding it outright would make the Factacy call fail silently (error is `console.log`ged) on every tenant. Unlike `currency_api_key`, a consumer exists.

## Fix (option B, tenants only)
- `src/core/guards/cockpit-caller-key.guard.ts`: when a valid `x-internal-api-key` is presented, set `request.cockpitCallerVerified = true`. A log-mode keyless / wrong-key call is still answered but not marked; `off` mode marks nothing.
- `src/modules/global/global.service.ts`: `KEYED_CALLER_ONLY_GLOBAL_SETTINGS = ['factacy_api_key']`; `getTenantSettings(hostName, callerVerified = false)` skips those rows unless `callerVerified`.
- `src/modules/global/global.controller.ts`: passes `req.cockpitCallerVerified === true`.
- `src/modules/global/module.spec.md`: rule documented; `factacy_api_key` removed from the "still open" list.
- The backend already sends the key (`4acb1de1`, `CORS_ORCHESTRATION_INTERNAL_API_KEY` or `AI_CREDITS_INTERNAL_API_KEY`).
- Contract schema and generated types unchanged: the key is still a delivered key for the backend (`check-tenant-contract.py`: consumers consistent), so nothing to sync to backend/frontend.

## Tests
- `tenant-verification.contract.spec.ts` (3 cases): unverified/default caller gets no `factacy_api_key` but other settings; verified caller gets it; `currency_api_key` never delivered.
- `cockpit-caller-key.guard.spec.ts` (3 cases): valid key marks the request in log and enforce mode; log-mode keyless / wrong key is answered but unmarked; off mode never marks.
- With the fix disabled, 2 of the 6 new tests fail (unverified withholding, valid-key marking); with it, all pass.

## Verification
- `npm run gates`: lint, test, test-floors, build, unguarded-routes all exit 0 (ESLint: 0 errors). Global + guard suites 20/20 (module-wide 52/52 before the new tests).
- NOT done: a live call against a running cockpit.

## Consequences / follow-ups
- A backend deployment WITHOUT the internal key configured no longer receives `factacy_api_key`, so its Factacy AI news goes silently empty until the key is set. Check the cockpit's `log`-mode lines (`SAN-44 S7 [log mode] missing x-internal-api-key`) for such deployments before deploying.
- Production `TENANT_SETTINGS_KEY_MODE` was not checked. End state: `enforce` once every backend sends the key.
- Rotate `factacy_api_key` after this is deployed to production (`docs/SECRET-ROTATION-LOG.md` row 3, SAN-1562); the key must be treated as compromised.
- Remove the `test.fail()` in sc-saas-e2e `tests/api/tenant-contracts.spec.ts` after deploy (repo not in this workspace).

## Commit
Not committed yet. Push branch: `ai_native_setup_sandeep`.
