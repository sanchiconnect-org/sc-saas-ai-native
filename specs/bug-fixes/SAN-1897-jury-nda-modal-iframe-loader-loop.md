# SAN-1897 — Jury NDA modal takes ~47 s to open (gate page nests itself through /iframe_loader)

Linear: https://linear.app/sanchiconnect/issue/SAN-1897 · Repo: `sc-saas-admin` · Priority: Medium · Assignee: Sandeep
Classification: **CODE_ERROR**

## Problem
A juror with an unsigned Mandatory NDA opens the round and sees only the NDA placeholder. The modal, the only way to sign, appears ~47 s later (dev, round 447 of program 480).

## Evidence (from the ticket)
Playwright with the jury session: DOMContentLoaded 0.8 s, ~70 aborted `/iframe_loader` requests, `load` at 47.1 s, modal at 47.5 s. `GET /iframe_loader` as the juror answers `302 → /jury/nda/program/480/round/447`. The P5 e2e test "NDA modal opens within 15 s" is `test.fail` until fixed.

## Root cause (verified in code)
1. Every admin page renders the hidden master-data iframe `src=/iframe_loader` (`themes/default/html/elements/footer.php:31`), including the NDA gate page `jury/nda.php`.
2. `juryNdaGateDecide()` only exempts the first route segments `auth`, `logout`, `404`. `iframe_loader` resolves as "unresolvable", and while the juror has a blocking Mandatory round the decision is `default_deny`.
3. `enforceJuryNdaGate()` shows the modal in place only for reason `nda_required`; `default_deny` on a GET redirects to the NDA entry page. So the iframe is redirected to the gate page, which contains the same iframe, and so on (frames nest and abort; each nested gate also does `POST /jury/nda`).
4. The modal starts on `window.load` (`nda.php`), which fires only when the browser gives up.

## Fix (`sc-saas-admin` only)
- `includes/jury_nda_functions.php`: `juryNdaGateDecide()` treats the first route segment `iframe_loader` as a neutral route (allow, reason `neutral_route`). `modules/iframe_loader.php` is a static "Loading..." stub and renders no application data.
- `modules/jury/module.spec.md`: gate allow-list updated.
- Not changed (not needed once the loop is gone): modal still starts on `load`; footer iframe `src` unchanged.

## Verification
- `php -l includes/jury_nda_functions.php`: clean. `php tests/auth-gates.php`: 941 passed (floor 941), 0 failed.
- Throwaway DB-less harness (fake DB: juror allotted to a Mandatory round with no signature) calling `juryNdaGateDecide()` for a jury session:
  - before (HEAD): `iframe_loader` → DENY `default_deny` (the 302 in the ticket)
  - after: `iframe_loader` → allow `neutral_route`; `auth` unchanged; other routes (`some_other_page`, `dashboard`) still DENY `default_deny`, so the gate is not loosened for anything else.
- NOT done: live check on a real jury session / the 47 s timing, phpcs and phpstan (not installed locally), e2e run. No automated regression test added: the gate is a DB-backed PHP function with no test harness in this repo (the auth-gates test is a static check), so the harness above was throwaway.

## Follow-ups
- Deploy, then confirm the modal opens within a few seconds and remove the `test.fail` on the P5 test in `sc-saas-e2e` (repo not in this workspace).
- Other non-page helper routes that might also be default-denied for a blocked juror were not audited.

## Commit
Not committed yet. Push branch: `ai_native_setup_sandeep`.
