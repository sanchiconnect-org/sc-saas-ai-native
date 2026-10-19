---
id: SAN-1925
title: "Frontend fixes already written still firing — SAN-1869 not on main, stale PWA builds keep reporting fixed bugs (SC-SAAS-FRONTEND-H0/H1, 2J, 17)"
type: bug-fix
status: todo
linear: https://linear.app/sanchiconnect/issue/SAN-1925
sentry: [SC-SAAS-FRONTEND-H0, SC-SAAS-FRONTEND-H1, SC-SAAS-FRONTEND-2J, SC-SAAS-FRONTEND-17]
repos: [frontend]
related: [SAN-1869, SAN-1898, SAN-1673, SAN-598, SAN-1140, SAN-589]
commit: none — deploy/release action, no code change
created: 2026-10-15
updated: 2026-10-15
---

# SAN-1925: fixed in code, still firing in prod

## Investigation
Production runs `sc-saas-frontend@218edca78`, which is `origin/main` HEAD (merge of PR #1938, 2026-10-11 20:41 IST). It was checked with `git merge-base --is-ancestor`.

**1. Fixed, but not on `main` (deploy lag)**
* H0 (26 events / 5 users) and H1 (16 / 5): `public-profile-dynamic-single-form-view` `s.fields.find` on undefined, on release `218edca78`.
* The fix, SAN-1869 `c42bf95be`, is on `ai_native_setup_vishali` but is **not** an ancestor of `origin/main`, `origin/development` or `218edca78`.
* The sibling fix SAN-1898 `3914468c8` is in the same state.
* `ai_native_setup_vishali` is 79 commits ahead of `origin/main`.

**2. Fixed and on `main`, but old PWA builds keep reporting**
* 2J: unhandled 401 (`meetings/pending-acceptance`, `connections/requests/received`), 2,837 events / 1,098 users all-time.
  * The SAN-1673 fix `bd95b012c` **is** in `218edca78`.
  * Events by release over the last 7 days: ~118 from stale builds and only 1 from `218edca78`.
  * The stale builds are `51eb6706` (2026-08-18), 31 events; `bcf88383d`, 25; `dab63831` (2026-09-03), 14; and about 10 others.
* 17: lightGallery `0000-0000-000-0000` licence key. The SAN-598 fix (`licenseKey: 'GPLv3'`, `e5280e7f2`, `96ea39cb1`) is on `main`, so only pre-fix builds can raise it.

## Fix
No code change. Actions:
1. Promote `ai_native_setup_vishali` → `development` → `stagingdemo` → `main` and redeploy prod.
2. Check why PWA clients stay on August builds. SAN-1140 (SwUpdate handling) is Done, but `git log --all --grep=SAN-1140` finds no commit. Confirm the update prompt actually ships in `218edca78`.
3. Do not reopen the per-bug tickets.

## Verification
After the deploy, H0/H1 should stop on the new release tag. 2J and 17 should fall to zero once stale clients update.
