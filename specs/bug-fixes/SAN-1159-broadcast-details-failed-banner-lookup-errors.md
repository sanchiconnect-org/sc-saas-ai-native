# SAN-1159 — Broadcast details: misleading "in progress" banner; stats lookup errors hidden

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1159
- **Repo:** sc-saas-admin · **Priority:** Medium · **Assignee:** Nirmal Singh · **Related:** SAN-1154
- **Classification:** CODE_ERROR

## Problem (seen on local dev, broadcasts 29/33/35/37)
1. Broadcast 29 had 4/4 recipients Failed, yet the page said "Email delivery is in progress and the status will be
   updated shortly." The template showed that text whenever no row had an SES message id, and failed rows never get one.
2. On broadcasts 33/35/37 the emails were received, but Request Stats ended with "Done" and rows stayed "Sent" with
   no times. Every `getEmailStats` lookup had failed, but the SES error was only in a per-row hover tooltip.
3. Failed rows gave no reason.

## Fix
- `modules/broadcast_messages/details.php`: per-row `failReason` for `failed` rows, taken from `ses_email_queue.response`
  (the queue sender stores the caught error there). It uses the first readable `message`, capped at 300 characters.
- `themes/default/html/broadcast_messages/details.php`:
  - The header message depends on row states: queued rows → "in progress"; all failed → "Sending failed for all
    recipients. Hover over a row to see why."; sent without an SES message id → "Delivery stats aren't available…".
  - Failed rows get the reason as a `title` tooltip (HTML-escaped).
  - Request Stats collects lookup errors per run and ends with "Stats unavailable for N of M — <first error>" (the full
    breakdown is on hover), or "Done — N not indexed by SES yet…", instead of a bare "Done".
  - Layout: "All Recipients" and Request Stats share the first header line. All status/alert text (Request Stats
    result, "not indexed yet", and the in-progress/all-failed/no-stats banners) sits on its own full-width line
    below, where a long SES error wraps. Before, it was inline between the title and button, wrapping the title and
    squashing the button. The two script-toggled alerts are plain block `<div>`s, not `.d-block`, whose `!important`
    would defeat jQuery `show()`/`hide()`.
- Confirmed on local dev: the summary surfaced `AccessDeniedException … user/SanchiSaasDevS3 is not authorized to perform:
  ses:GetMessageInsights`. That's the IAM permission in the dev account, not a code issue.

## Verification
- `php -l` clean on both files; `node --check` clean on the page script; no `//` comments.
- jsdom run of the real page script: with lookups returning AccessDeniedException, the run ends with
  "Stats unavailable for 6 of 7 — AccessDeniedException: User is not authorized to perform ses:GetMessageInsights".
- Not yet re-tested in the browser on local dev. sc-saas-admin has no automated tests.

## Commit
sc-saas-admin `367a3d70` (on `ai_native_setup`)
