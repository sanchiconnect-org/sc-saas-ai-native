---
id: SAN-1876
title: "SC-SAAS-ADMIN-5 Too many connections — remaining events are bot probes on dev servers"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1876
sentry: [SC-SAAS-ADMIN-5]
repos: [admin]
commit: sc-saas-admin@a834a578 (branch ai_native_setup_vishali, pushed)
created: 2026-10-12
updated: 2026-10-12
---

# SAN-1876: admin bot probes reaching the DB bootstrap

**Classification:** ENV_ERROR / hardening.

## Investigation
* **Production is fixed by SAN-1736.** Production events dropped from 327/day to 0/day from 2026-10-07, and the retry helper appears in the current stack.
* Every event since then is `environment: local` on `adm.*.sanchidev.in`. They come from crawlers and AI bots probing `/@fs/...`, `/__vite_*`, `*.json`, `*.yml` and `*.tfstate`.
* Those paths don't exist, so they fall through to index.php, which opens two DB connections before it can return 404.

## Fix
`sc-saas-admin/.htaccess` gets two `!-f`-gated rules after the SAN-140 dotfile rule:
* `^(@fs/|__vite)` → 404
* `\.(json|ya?ml|env|tfstate|ini|sql|bak)$` → 404

No admin route uses these prefixes or extensions.

## Verification
On the local XAMPP vhost `admin.localhost`, after `httpd -t` returned Syntax OK:
* The probe URLs return 404.
* `/` → 302, `/auth/login` → 200, `/table/application_programs` → 302, `/.git/HEAD` → 403, and the real `composer.json` → 200, all unchanged.

No test framework exists in this repo.

## Note
`/composer.json` is publicly readable, which is a minor information leak and out of scope here.
