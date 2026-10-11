# SAN-1839 — Replace NDA with "must sign again": no sign that the re-sign e-mails went out (reported as http_502)

- Linear: https://linear.app/sanchiconnect/issue/SAN-1839 (Enhancement, milestone "Jury NDA Signing", Bug + Repo: Admin, Sandeep; still In Progress)
- Repos touched: sc-saas-admin and (supporting change) sc-saas-backend. Classification: CODE_ERROR for the invisible failure; the cause of the 502 itself is NOT confirmed (ENV_ERROR suspected on the backend host).

## Problem
After Replace with "Yes - they must sign the new version again", the admin saw only "NDA document replaced"; the juror got no re-sign e-mail. Once the outcome was shown, the toast read `http_502`.

## Evidence
- `juryNdaReplaceVersion()` already calls `juryNdaNotifyResign()` and returns `notification`; the page script ignored it.
- The 502 is a gateway answer from the backend host; the backend route, DTO and service logic show no 502 source. The backend sent its recipients one after another, several seconds each, which can outlast a proxy / the 30 s caller timeout.

## Fix
- Admin: the page shows the real outcome (N jurors e-mailed, or an error toast with the reason code and the hint to use "Send reminder to selected"); `notification` now carries `attempted` and `signers`; reason and counts go to the PHP error log and to the `nda_resign_triggered` audit entry; `juryNdaSendNotification()` retries up to 3 times (1 s, 2 s) on 502 / 503 / refused connection, never on 504.
- Backend: `sendJuryNdaNotificationEmail` sends recipients in parallel groups of 5, same response shape and order (new jest test).
Files: `sc-saas-admin/includes/jury_nda_functions.php`, `.../edit_program_round.php`, `.../module.spec.md`; `sc-saas-backend/src/modules/global/admin-actions/admin-actions.service.ts` (+ spec), `.../jury-nda/module.spec.md`.

## Verification
Admin: `php -l`; CLI checks of `juryNdaNotifyResign` outcomes and of the retry against a local HTTP mock (flaky twice then ok recovers on attempt 3; always 502 ends `http_502` after 3 attempts; 504 not retried). Backend: `npx tsc --noEmit` clean, 21 notification tests pass. NOT done: a real Replace on an environment with a working backend; the backend change is not deployed.

## Next
Run Replace (Yes) again and read the toast; if `http_502` persists, read the backend process status and its log around `sendJuryNdaNotificationEmail`. Jurors already in Re-sign required are not e-mailed again by Replace; use "Send reminder to selected".
