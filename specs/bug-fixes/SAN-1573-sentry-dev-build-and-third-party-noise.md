# SAN-1573 — Stop Sentry ingesting dev-build and third-party noise at source (sc-saas-frontend)

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1573 · successor to the cancelled SAN-446 · related SAN-158, SAN-598, SAN-1623

## What was still arriving (Sentry, last 30 days, 15 Oct 2026)
| Noise | Events | Source | Action |
|---|---|---|---|
| `[webpack-dev-server]` warnings | none since 29 Sep | filtered earlier (SAN-168..184) | — |
| lightGallery licence warning (FRONTEND-17) | 65 prod + 249 dev | every recent event from builds before `e5280e7f2` (SAN-598, 5 Oct, licence key on all 14 galleries) | none; stops as stale cached clients refresh |
| moment deprecations | 0 | — | — |
| `[ngx-ui-loader] - loaderId "…" does not exist.` (FRONTEND-11, 5Y) | 128 prod + 42 dev | current code: start()/stop() with no matching loader on screen; harmless warning | **filtered** |
| NG0100 ExpressionChanged… (9M, B2, BV) | ~70, dev builds only | Angular dev-mode check; never runs after enableProdMode() | **filtered in non-production builds** |
| developers' `ng serve` sessions | — | localhost / 127.0.0.1 | **filtered** |

## Change
`src/main.ts`, `Sentry.init` → `beforeSend`, three narrow rules after the webpack-dev-server one:
1. `location.hostname` is `localhost` or `127.0.0.1` → drop. Deployed dev servers (thub.sanchidev.in …) still report.
2. `!environment.production` and the exception value contains `NG0100` → drop. Production builds are unaffected.
3. No exception, level `warning`, message starts `[ngx-ui-loader] - loaderId "…" does not exist.` → drop. The thrown
   `loaderId "master" is duplicated` crash is an Error, so it is still reported (SAN-1623).

## Limits
- A `beforeSend` filter only exists in builds that contain it. Clients running an older cached bundle keep sending until
  they reload (see SAN-1140 / SAN-1624).
- Dev-server events are still tagged `environment: local`; tagging them correctly is SAN-158 (parked).

## Verification
- 10 cases from real Sentry messages run against the same expressions: drops (laptop, NG0100 on thub, both
  ngx "does not exist" forms incl. URL-suffixed and `connect-button-*`) and keeps (thrown "is duplicated", production
  NG0100 text, real production and dev-server TypeErrors, other warnings): all pass. `main.ts` has no unit-test
  harness, so this is a script, not a committed test.
- `tsc -p tsconfig.app.json --noEmit` clean; `ng build --configuration production` succeeds.
