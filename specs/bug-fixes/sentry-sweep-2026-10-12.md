---
title: "Sentry sweep 2026-10-12 — sc-saas-admin + sc-saas-backend (14d unresolved)"
type: triage-sweep
date: 2026-10-12
owner: vishali kashyap
linear_project: Production Defects (milestone M5)
tickets: [SAN-1872, SAN-1873, SAN-1874, SAN-1875, SAN-1876]
not_filed: [SAN-1871 (already open, Aman), SC-SAAS-TENANTS-2, SC-SAAS-TENANTS-ADMIN-4]
repos_touched: [sc-saas-backend, sc-saas-admin]
commit: sc-saas-backend@acfeb44a (SAN-1872), sc-saas-backend@1ad29b33 (SAN-1874), sc-saas-admin@a834a578 (SAN-1876) — all on ai_native_setup_vishali, pushed
---

# Sentry sweep: 2026-10-12

This sweep covers the 14-day unresolved Sentry issues for the three projects in the Sentry link. Only sc-saas-admin and sc-saas-backend had any; the third project ID had none.

* There were 7 unresolved issues.
* 5 new Linear tickets were filed, all assigned to Vishali.
* 1 issue pair already had an open ticket.
* Code changes in 2 repos: **nothing committed or pushed**.

## 1. Outcome per issue

| Sentry | Linear | Classification | What it really was | Action | State |
|---|---|---|---|---|---|
| BACKEND-3M | SAN-1872 | CODE_ERROR | `profile-views/increment` writes an unsanitised `userId` from the request body. A NaN reaches mysql2 unquoted and produces "Unknown column 'NaN'". The previous ticket SAN-1754 was closed with no code change. | Backend fix (local) | In Review |
| BACKEND-9 | SAN-1874 | ENV_ERROR | S3 `SignatureDoesNotMatch`, about 1–2 events a day, so intermittent. SAN-454 was closed without the prod AWS check ever happening. | Diagnostic tagging (local) and a prod AWS check | In Review |
| ADMIN-5 | SAN-1876 | ENV_ERROR / hardening | Production is already fixed by SAN-1736: production events have been 0 a day since 10-07. The remaining events are bots probing for secrets on the `*.sanchidev.in` dev servers, and each probe reaches the DB bootstrap. | `.htaccess` deny rules (local) | In Review |
| BACKEND-X | SAN-1873 | unknown, deploy-gated | AxiosError 500 unhandled rejection. The SAN-988 cron wrapper is deployed and the error persists, so the source is elsewhere. The SAN-455 host tagging reached `main` only on 10-11. | Wait for deploy, then fix the named call site | Todo (blocked) |
| BACKEND-4X | SAN-1875 | deploy lag | The SAN-1663 fix reached `main` only on 10-11 (PR #2027). Events still show the pre-fix wording, and the container started 10-03. | Redeploy, verify, resolve | Todo (blocked) |
| BACKEND-4Q / 5N | SAN-1871 (existing) | data | Broken Handlebars in the tenant DB template `pending-connection-reminder`. | Not re-filed. Open with Aman since today. | — |

**Out of the link's scope** (seen in the org-wide list, not filed):
* SC-SAAS-TENANTS-2 (assigned to Aman in Sentry)
* SC-SAAS-TENANTS-ADMIN-4 (same 1040 pattern as ADMIN-5, previously SAN-1757)

## 2. Code changes (uncommitted)

| Repo / branch | File | Ticket | Change |
|---|---|---|---|
| sc-saas-backend / `ai_native_setup_vishali` | `src/modules/user/repositories/user.repository.ts` | SAN-1872 | `trackProfileView()` passes `userId` and `profileId` through `toPositiveIntOrNull()`. Anything that is not a positive integer is stored as NULL (an anonymous view). |
| sc-saas-backend / `ai_native_setup_vishali` | `src/instrument.ts` | SAN-1874 | New `attachAwsSignatureError()` in `beforeSend`. It tags `aws_region`, `aws_hostname`, `aws_status` and `app_domain` on `SignatureDoesNotMatch` events only. |
| sc-saas-admin / `ai_native_setup_vishali` | `.htaccess` | SAN-1876 | Two `!-f`-gated rules return 404 straight from Apache for `^(@fs/\|__vite)` and for missing `*.json/yml/yaml/env/tfstate/ini/sql/bak` paths. |

Diff size: backend +50/−2 across 2 files; admin +11 in 1 file.

## 3. "No flow breaks": evidence per change

### SAN-1872: profile view tracking
**Writer:** the only caller chain is `POST user/profile-views/increment` → `UserService.trackProfileView` → `UserRepository.trackProfileView`. `profileId` there is always a DB id, so it's unaffected.

**What changes in the database:**
* Today, anonymous viewers send `userId: ''`. Production MySQL runs non-strict: there were zero "Incorrect integer value" events in 90 days, so these rows are being stored as `user_id = 0`.
* After the fix, the same visit is stored as `user_id = NULL`.
* Valid logged-in ids, including numeric strings like `"5"`, are stored exactly as before.

**Every reader was checked.** There are only three, all in sc-saas-backend; there are no readers in admin, tenants, tenants-admin or the analyzer.

| Reader | Behaviour with `0` (today) | Behaviour with `NULL` (after) | Same? |
|---|---|---|---|
| `getProfileViewsCount2` (DISTINCT userId) | one anonymous bucket | one anonymous bucket | yes |
| `UserRepository.getProfileViewers` (LEFT JOIN users, GROUP BY user.id) | no user row matches 0, so the NULL group shows as "Unknown User" | NULL group, shown as "Unknown User" | yes |
| `NotificationCountersRepository.getProfileViewsWeekly` (INNER JOIN users) | excluded | excluded | yes |

**Contract and UI:**
* The DTO and route are unchanged, so there is no API contract change.
* The frontend viewer modal already renders a null viewer as "Unknown User".
* `@IsInt()` was deliberately *not* added: it would 400 every anonymous view and show logged-out visitors an error toast.

**Pre-existing, not introduced here:** clicking an "Unknown User" row opens `/undefined/profile/null` (`profile-viewers.component.ts → openDetailsView`). This already happens for every anonymous row today. It is a candidate frontend follow-up and wasn't touched here, because the ticket is scoped to the backend.

### SAN-1874: Sentry `beforeSend`
The real `beforeSend` was exercised by capturing it from `Sentry.init` in a scratch script:

| Input | Result |
|---|---|
| S3 `SignatureDoesNotMatch` with existing tags and an `accessKeyId` on the error | Existing tags kept; region, hostname, status and app_domain added; **accessKeyId not attached** |
| Another AWS error (`NoSuchKey`) | Untouched |
| AxiosError | The existing SAN-455 host/method/status tags still applied |
| Plain `Error`, no hint, a string exception | Untouched, no throw |

* The event is never dropped and grouping/fingerprint are unchanged.
* Diagnostic only: no runtime behaviour of the API changes.

### SAN-1876: admin `.htaccess`
Live test on the local XAMPP vhost `admin.localhost`, after `httpd -t` returned Syntax OK:

| URL | Before (expected) | After |
|---|---|---|
| `/` | 302 to login | 302 |
| `/auth/login` | 200 | 200 |
| `/table/application_programs` | 302 | 302 |
| `/.git/HEAD` | 403 (SAN-140 rule) | 403 |
| `/composer.json` (real file) | 200 | 200 |
| `/@fs/proc/self/environ`, `/__vite_rsc_findSourceMapURL`, `/secrets.yml`, `/terraform.tfstate`, `/firebase-service-account.json` | routed to index.php, which opened 2 DB connections | **404 from Apache** |

The whole app was searched for URLs these rules could catch:
* No `@fs/` or `__vite` references.
* Every `.json`/`.sql` hit is a filesystem path or a download filename, served through extensionless routes. Examples: `whatsapp_templates.json` is read via `file_get_contents` and exported via `?submitAction=exportJson`; `adminer.sql` is Adminer's import file name.
* All admin routes are extensionless.

## 4. Test and type-check results (sc-saas-backend)

**Type check:**
* `tsc --noEmit` reports exactly **1 error**, and it is pre-existing: `sync-broadcast-email-stats.service.ts` cannot find `@aws-sdk/client-sesv2`. The package is declared in `package.json` (3.600.0) but is not installed in the local `node_modules`.
* The two touched files compile clean.

**Full Jest suite, run twice:** once with the changes and once with them stashed (the original code).

| Run | Suites failed / passed | Tests failed / passed |
|---|---|---|
| Original code (stashed) | 17 / 55 | 20 / 931 |
| With these changes | 16 / 56 | 19 / 932 |

* The failing suites are identical in both runs except `partner-domain-access.service.spec.ts`. That suite failed on the *original* code on a wall-clock TTL assertion (`ttl <= TOKEN_TTL_MS`), so it's flaky and unrelated.
* All other suite failures come from the same missing `@aws-sdk/client-sesv2` module (28 occurrences).
* **No regression from these changes.** Run `npm ci` in sc-saas-backend locally to get the full suite green.

**Other checks:**
* The `user.repository*.spec.ts` suites pass (5/5).
* ESLint shows no new findings on the touched files. The CRLF prettier errors come from the `core.autocrlf=true` checkout and are pre-existing.
* No new regression test has been written yet. Proposed: `user.repository.spec.ts` asserting `''`, NaN, `'abc'` and 0 → NULL, and `5`/`'5'` → 5. It is waiting for go-ahead.

## 5. Contract and invariant checks
* **API contract (invariant 2):** no controller or DTO changed, so there is nothing to audit in the frontend or admin.
* **Flags (invariant 1):** none touched.
* **Auth (invariant 4):** none touched.
* **Tenant scoping (invariant 5):** backend is one deployment per tenant, and the changes add no queries. The admin change sits before tenant DB selection and only rejects non-existent probe paths.

## 6. What happens next
1. Vishali reviews the local diffs.
2. Commit and push to `ai_native_setup_vishali` in sc-saas-backend and sc-saas-admin, plus these docs in the workspace repo on `ai_native_setup`. **Only on her go-ahead.**
3. Redeploy the backend from `main` (or later). This clears 4X (SAN-1875) and enables the BACKEND-X host tagging (SAN-1873) and the BACKEND-9 tagging (SAN-1874).
4. After deploy:
   * read `axios_host` on the next BACKEND-X event and fix that call site
   * use `app_domain`/`aws_hostname` on BACKEND-9 to target the prod AWS env check
   * confirm that 3M's profile_views events stop
5. Ship the admin `.htaccess` to the dev servers, then resolve ADMIN-5.

Per-ticket detail: `SAN-1872-*.md` … `SAN-1876-*.md` in this folder.
