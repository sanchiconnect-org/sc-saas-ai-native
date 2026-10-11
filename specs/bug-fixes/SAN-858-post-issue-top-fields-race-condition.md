---
id: SAN-858
title: "Post Issue top fields silently lost when adding/editing a stakeholder"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-858
repos: [admin]
commit: sc-saas-admin@59c2c022
created: 2026-09-19
updated: 2026-09-19
---

# SAN-858 — Post Issue top fields lost on stakeholder add/edit

## Symptom

On `portfolio_management/round/post_issue/:uuid`, "No. of new shares issued", "Market Value per share",
"Issue Price per share", and "Issue Date" appear empty on page load and after adding/editing a stakeholder.

## Root cause (CODE_ERROR — race condition)

`themes/default/html/portfolio_management/round/post_issue.php`'s `#addCap`/`.editCap` handlers open a
stakeholder iframe modal; on `postMessage` (stakeholder saved), the old code did:

```js
$(".submitFormBtn").click();
window.location.href = data.redirectUrl;
```

`.submitFormBtn`'s click handler saves the top fields via an **async** `$.ajax()` POST
(`submitAction: editPostIssue`). The very next line navigates immediately — the browser aborts the in-flight
POST before the server ever processes it, so `issued_shares`/`share_market_value`/`issue_price`/`issue_date`
never actually reach `portfolio_rounds`. The controller (`modules/portfolio_management/round/post_issue.php`)
re-fetches `$getRound` fresh on every GET, so the reloaded page correctly shows the DB's (still-empty) values —
the bug is the save never happening, not a display/read bug.

## Fix

Extracted the save into `savePostIssueTopFields()`, returning the `$.ajax()` promise with no navigation of its
own. `#addCap`/`.editCap`'s `postMessage` handlers now `.always()` wait for that promise to settle before
navigating to `data.redirectUrl`. The `.submitFormBtn` click handler keeps its original UX (Swal success/error +
navigate to `resp.editUrl`), now wired via `.done()`/`.fail()` on the same function instead of inline.

## Verification

`php -l` clean. Extracted and validated the script block's JS syntax (PHP tags stripped) with `node --check` —
clean, both before and after the edit. No test framework in this repo (per `sc-saas-admin/CLAUDE.md`) — manual
QA needed: fill the top fields, click "+ Add" to add a stakeholder without clicking Submit first, and confirm
the top fields persist across the reload.

## Rollout

Committed and pushed to `ai_native_setup`: `59c2c022`.

## Open questions

None blocking.
