# SAN-1146 — Clarification Pending: count, filter and list modal (startups + program applicants)

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1146
- **Repos:** sc-saas-admin, sc-saas-backend · **Assignee:** Nirmal Singh
- **Classification:** FEATURE
- **Note:** the Linear issue carries only the `Repo: Admin` label, but backend commits shipped under it too (see Commits).

## Change
**sc-saas-admin**
- **Startups table** (`8eb26c99`): a "Clarification Pending" badge linking to a `clarification_pending` pseudo-condition,
  which CSV export also honours. Final rule after iterations (`be066c1d` → `2ef459f4`): `approval_status = submitted
  AND followup = 1`, matching the public-portal registration bucket.
- **Programs table:** Program Stats shows a Clarification Pending count (submitted + pending + `followup=1`).
- **Application management** (kanban + tableview): a Clarification Pending option in the Evaluation Status filter, plus a
  header count badge.
- **Shared list modal** (`99b19f93`): `themes/default/html/partials/clarification-pending-modal.php`.
  - Shows company, email, follow-up notes and date, with in-modal search.
  - Backed by `getClarificationPendingList()` in `core_functions.php`.
  - Applicant handlers reuse the partner/program-manager access checks (`canAccessProgramApplications`).
  - Program applicant counts include drafts tagged Draft/Submitted; soft-deleted rows are excluded.
- **Startup detail** (`fb431210`): the Flag (clarification) action is hidden for approved, rejected and limited_access
  startups.
- **Fix found on the way:** the startups badge never rendered, because `sparkAdminTpl` has no `__isset`, so `isset($this->x)` is
  always false in templates.

**sc-saas-backend** (public-portal registration summary + lists; `410bce74` → `0d52fab0`)
- `clarification_pending`: `approval_status = submitted AND followup = true`.
- `under_process`: `approval_status = submitted AND followup = false`.
- `total_applications` = the union of approved, rejected, under_process and clarification_pending, so the buckets always
  sum to the total. Pending, not_qualified and limited_access are excluded.

## Verification
- `php -l` / build clean per commit. Admin and backend conditions were cross-checked to match. No automated tests
  were added.

## Commits
sc-saas-admin `8eb26c99`, `99b19f93`, `be066c1d`, `fb431210`, `2ef459f4` · sc-saas-backend `410bce74`, `0d52fab0`
(on `ai_native_setup`)
