# SAN-1758 — frontend offers sales/hiring pitch the backend removed (Canceled, NOT fixed)

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1758 (status Canceled; Sentry SC-SAAS-FRONTEND-GM, -7T, -ET) · **Repo:** sc-saas-frontend + sc-saas-backend · **Priority:** High · **Assignee:** Aman kabra · **Classification:** PRODUCT_DECISION

## Evidence
- Frontend `PitchDocumentTypes` = `fundraising-pitch | sales-pitch | hiring-pitch`; backend = `fundraising-pitch | pitch-document` (observed in code).
- Backend removed sales/hiring on purpose in `d4fd191b` (May 2023): enum values, every `sales_*`/`hiring_*` column of `StartupPitchDeckEntity`, repository methods (observed in git).
- GM: 2 events / 1 user (observed in Sentry).
- The frontend also calls routes the backend does not serve: `PATCH startup/pitch-deck/power-pitch` (commented out), pitch-deck `supporting-documents` routes, `compile/...` (observed).

## Root cause
Frontend UI and backend contract diverged in 2023; the frontend still exposes a feature with no backend.

## Fix
None. An additive backend enum change was tried and REVERTED: the DELETE route ignores the type (a sales delete would wipe the fundraising document), a pitch-video upload would overwrite the fundraising video, and `savePitchDocument`'s switch only handles fundraising (200 with `undefined`). No code change is left in any repo.

## Not fixed / decision needed
(A) rebuild sales/hiring in the backend (columns, repository, switch, per-tenant migration) or (B) remove them from the frontend UI. Recommendation: B. Needs the product owner / dev lead.

## Contract impact
None as committed. Option A would change the backend contract (DTO enum, entity schema, migrations for every tenant DB).

## Verification
Code and git history reading only; the reverted attempt is in no commit.

## Commit
None.

## Sentry
GM resolved with a reopen-if-it-grows note; 7T and ET resolved as noise.
