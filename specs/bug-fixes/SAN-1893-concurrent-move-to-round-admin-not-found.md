# SAN-1893 — Concurrent "Move to Round" by the same admin fails with "Admin not found. Please try again."

- Linear: https://linear.app/sanchiconnect/issue/SAN-1893 (found by sc-saas-e2e smoke journey 5, SAN-1576; assignee Sandeep; label Bug + Repo: Admin)
- Repo: sc-saas-admin only. Classification: CODE_ERROR (race condition).

## Problem
Several `moveApplicationToNextRound` requests of one admin at the same time: one succeeds, the others answer HTTP 200 with "Admin not found. Please try again.". Sequentially all succeed. The application stays in its round.

## Root cause
`generateRandomStringForBackdoor()` (`includes/core_functions.php`) writes a fresh random token into ONE column, `spa_admin_users.auth_token`, on every call, and the backend accepts only the token that is stored at that moment (`checkIsValidAdmin`: `AdminUsersEntity.findOne({authToken})`). Request A stores token A, request B stores token B, then A's backend call looks for token A and gets "Admin not found". `generatePartnerRandomStringForBackdoor()` is worse: every partner session writes the same developer row.
~259 call sites use these two generators, so the fix is in the generators, not in the move handler.

## Fix
New `acquireBackdoorTokenLock($database, $rowId)`: a MySQL named lock (`GET_LOCK`, name = hash of tenant database name + token row id) taken before the token is rewritten and kept until the end of the PHP request (released by a shutdown function, and by MySQL when the connection closes). Requests of the same admin take turns: the second waits until the first has finished its backend call. Wait at most 25 s; if the lock cannot be had the request goes on as before, so it can delay but never block. Re-entrant within a request. The partner generator locks the developer row it writes.
Files (uncommitted): `sc-saas-admin/includes/core_functions.php`, `sc-saas-admin/includes/partners_functions.php`.

## Verification
- Real MySQL 8 (a throwaway instance, outside the product DB) and 3 simultaneous PHP processes of ONE admin, each simulating a 1.2 s backend call that checks the stored token: WITHOUT the lock (old behaviour) 2 of 3 got ADMIN-NOT-FOUND (1 ok); WITH the lock 3 of 3 ok, taking turns (1.2 s, 2.4 s, 3.6 s). Three DIFFERENT admins ran in parallel (1.2 s each), so unrelated admins do not wait for each other.
- `php -l` on both files. `bash scripts/gates.sh` in sc-saas-admin: platform, php-lint, auth-gates, ai-credit-writes pass; the composer gate fails on this machine ("Timezone database is corrupt" when composer starts) and phpstan / phpcs are not installed here, so those three could not run.
- NOT done: Journey 5 with `--repeat-each=3` on the development tenant (needs the deployed fix and the sc-saas-e2e setup); no automated test in sc-saas-admin (no test framework).

## Trade-offs
Concurrent backend calls of one admin are now serialized, so three simultaneous moves take about three times as long as one; a waiter that cannot get the lock within 25 s proceeds without it (old behaviour). Direct token writers outside the two generators (e.g. the backdoor-login link builders) were not changed.

## Commit
Not committed (branch ai_native_setup_sandeep).
