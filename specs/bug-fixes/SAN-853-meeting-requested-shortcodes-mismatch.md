---
id: SAN-853
title: "meeting-requested template's View Details link/shortCodes mismatch"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-853
repos: [backend]
commit: sc-saas-backend@b7f89db2 (branch ai_native_setup_vishali, pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-853 — meeting-requested View Details link / shortCodes consistency

## Problem
Investigating a report of a broken "View Details" button and a stray "{ }" artifact near the logo in the "[Meeting] Meeting requested" email (`meeting-requested` template) surfaced a separate, confirmed inconsistency: the template's `href` and its `shortCodes` metadata list referenced two different variables (`reschedule_link` in the button, `meeting_link` in the metadata list) — one of the two was always going to be undocumented.

## Root cause
CODE_ERROR — mismatch between the template body's `href="{{ reschedule_link }}"` and its `shortCodes` metadata (which only listed `meeting_link`), `sc-saas-backend/src/modules/global/admin/spa_email_templates.repository.ts` (~line 908-914). Confirmed via investigation:
- `shortCodes` is never read at runtime by `ses-email.service.ts`'s `sendMeetingRequestedEmail` — it only feeds the admin CMS's shortcode-insertion panel, so this mismatch was cosmetic/documentation-only, not the cause of the reported broken button.
- Both `reschedule_link` (→ `urlService.createAuthenticatedPendingMeetingUrl()`, the accept/reject/propose-time page) and `meeting_link` (→ `urlService.createAuthenticatedMeetingUrl()`, the meeting itself) are real, independently populated URLs in `meetings.service.ts`'s `sendMeetingRequestedEmail` call — either is a functioning link, they just point to different destinations.

**The actual "unclickable" bug was unrelated to this mismatch** — see SAN-854 (`createShortLink()` silently swallowing shortIo gateway failures).

## Fix — as actually applied
Two ways to resolve this mismatch were on the table: point `shortCodes` at `reschedule_link` (matching the button as it stood), or point the button at `meeting_link` (matching the existing `shortCodes` list). Vishali chose the latter directly in the admin/CMS seed content, committed as `sc-saas-backend@b7f89db2`: the template's `href` now reads `{{ meeting_link }}`, consistent with the unchanged `shortCodes` list. Confirmed post-fix: template body and `shortCodes` now agree, no mismatch remains.

Note for future reference: the button's accompanying copy still reads "Please accept/reject or propose a time for the same," which describes the `reschedule_link` destination rather than `meeting_link`. Flagged to Vishali; kept as-is per her explicit confirmation this fix is intentional and complete — not re-litigated further here.

The same commit also renamed the `meeting-reschedule-request` template's title from "[Meeting] Proposed Rescheule Meeting" to "[Meeting] Proposed Scheduled Meeting - To Receiver Meeting" (confirmed intentional, bundled into this commit).

## Blast radius
`sc-saas-backend` only, admin CMS seed content (`meeting-requested` and `meeting-reschedule-request` templates). No functional/runtime behavior change beyond which URL the "View Details" button targets.

## Verification
`npx tsc --noEmit` clean. No test framework covers email template string content.

## Related
[[SAN-854]] — the actual root cause of the reported "unclickable" button (`createShortLink()` silently swallowing gateway failures).
