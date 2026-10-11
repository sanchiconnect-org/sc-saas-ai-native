# SAN-1770 — Jury NDA decline email must reach the Program Manager(s) and the Super Admin(s)

- Linear: https://linear.app/sanchiconnect/issue/SAN-1770 (Enhancement project, milestone "Jury NDA Signing", assignee Sandeep, labels Feature + Repo: Admin)
- Repo: sc-saas-admin only
- Classification: CODE_ERROR (a gap against the requirement; the requirement itself is clear). Scope confirmed by Sandeep 2026-10-07: only the Mandatory decline email is needed.

## Problem
When a juror declines a Mandatory NDA, product wants an email to the programme's Program Manager(s) and to the Super Admin(s).

## Evidence
- `juryNdaAlertDecline()` already sends the backend `jury-nda-declined-admin` email (best effort, never blocks the decline).
- Its recipients come from `juryNdaRoundAdmins()` (`includes/jury_nda_functions.php`): `program_managers` plus holders of roles with `spa_admin_roles.can_view_jury_ndas = 1` (partner-matched). Super Admins were only included if their role row happened to carry that permission.

## Root cause
Super Admin was never added to the recipient list by role, so a tenant whose Super Admin role does not have `can_view_jury_ndas = 1` never got the alert.

## Fix
`juryNdaRoundAdmins()` now also adds every user of the Super Admin role (`spa_admin_roles.code = super_admin_role_id`) of the tenant: no partner filter, de-duplicated by e-mail (case-insensitive) with the PMs and permission holders, valid addresses only, juror excluded. A failed Super Admin lookup only drops those extra recipients. Decisions taken without a separate answer because the tenant DB makes them forced: "all Super Admin users of this tenant" and "decline reason included, same payload as for the PM".

Files changed (uncommitted): `sc-saas-admin/includes/jury_nda_functions.php`, `sc-saas-admin/modules/jury/module.spec.md`.

## Verification
- `php -l includes/jury_nda_functions.php`: no syntax errors.
- Throwaway CLI check of `juryNdaRoundAdmins` (fake DB, kept outside the repo): PM + Super Admins with duplicate (case-different) and invalid addresses; no PM; PM who is also Super Admin; juror listed as PM; partner programme; failed Super Admin lookup; Super Admin that also holds the permission. 7 of 7 pass.
- NOT done: a real decline on a test tenant to see the email arrive, and a check that the backend template renders. No automated test coverage added: sc-saas-admin has no test framework (noted gap, not bootstrapped here).

## Commit
Not committed (Sandeep commits/pushes on request; branch ai_native_setup_sandeep).

## Related change, same day (not part of SAN-1770)
The four Jury NDA emails now all carry the unsubscribe footer, and the signed-copy email has a Download button instead of an attachment (backend only, uncommitted); see the FA-010 spec section "Changes after approval".
