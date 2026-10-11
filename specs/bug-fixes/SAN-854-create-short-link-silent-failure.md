---
id: SAN-854
title: "createShortLink() silently swallows failures, leaving action links unclickable"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-854
repos: [backend]
commit: sc-saas-backend@72d1e346 (branch ai_native_setup_vishali, pushed)
created: 2026-09-18
updated: 2026-09-18
---

# SAN-854 — createShortLink() silent-failure fallback

## Problem
Reported symptom: the "View Details" button in a "[Meeting] Meeting requested" email (`meeting-requested` template) was completely unclickable — user confirmed "nothing happen on click, its unclickable".

## Investigation trail
This started from two symptoms reported against the `meeting-requested` template (broken button + stray "{ }" near the logo). Ruled out first:
- The template's `href="{{ reschedule_link }}"` was confirmed correctly formed and correctly wired to real code (`meetings.service.ts` passes `reschedule_link: otherUserAuthenticatedCalenderMeetingUrl.shortUrl`).
- The admin CMS's `shortCodes` metadata list omitting `reschedule_link` (fixed separately as SAN-853) was confirmed **not** to affect runtime rendering — verified by reading `sc-saas-admin/modules/ajax/email_actions.php`'s `edit_email_template` action, which saves `template_content` and `shortcodes` as independent fields with no cross-validation.

That left the actual value of `otherUserAuthenticatedCalenderMeetingUrl.shortUrl` at send time as the remaining suspect.

## Root cause
CODE_ERROR — `UrlService.createShortLink()` (`sc-saas-backend/src/core/services/url.service.ts`, ~line 74) calls the `sc-saas-3rdparty-webservices` shortIo gateway and silently swallows any failure:
```ts
} catch (error) {
  // console.log(error);
}
```
No return in the catch block means the function resolves to `undefined` on any gateway failure (network error, misconfiguration, timeout, non-2xx response). `createAuthenticatedPendingMeetingUrl()` then returns `{ shortUrl: undefined, whatsappUrl }`, and `meetings.service.ts` bakes that straight into the email's `reschedule_link` data field — producing an `<a href="">` or `<a href="undefined">` in the sent email. That renders as a styled button that does nothing when clicked, with zero error visibility anywhere (the only diagnostic line was a commented-out `console.log`).

This is not scoped to this one template — `createShortLink()` has ~30 call sites across `auth.service.ts`, `meetings.service.ts` (3 other meeting-link builders), `mentor.service.ts`, `investor.service.ts`, `import.service.ts`, `startup.service.ts`, `program-management.service.ts`, `corporate.service.ts`, `program-office-members.service.ts`, `service-provider.service.ts` — every one of them silently breaks its link the same way if the shortIo gateway has any hiccup.

## Fix
```ts
async createShortLink(originalUrl: string): Promise<string> {
  ...
  try {
    const apiResponse = await axios.post(...);
    auditServiceUsage(ServiceTypes.SHORT_IO, { originalUrl });
    ...
    return apiResponse?.data?.data || originalUrl;   // malformed/empty response -> fall back
  } catch (error) {
    this.logger.error({ method: 'createShortLink()', error: error.message });
    return originalUrl;                              // any failure -> fall back
  }
}
```
Falls back to the original (un-shortened but fully functional) long URL on any failure mode, and logs the error via `this.logger.error(...)` matching the convention already used in `aws-mediaconvert.service.ts` and `ses-email.service.ts`. Checked all ~30 call sites — none special-case a falsy `shortUrl`, so a real fallback URL is a strict improvement everywhere, not a behavior change any caller depends on.

## Blast radius
`sc-saas-backend` only — one shared method, used across meetings, auth, mentors, investors, imports, startups, program management, corporate, program-office-members, service-providers. No API/DTO/flag/tenant-scoping impact. Improves reliability of every shortened link platform-wide; does not change the long-URL destinations themselves.

## Verification
`npx tsc --noEmit` — no new errors. No test framework covers this service. Manual verification would require either forcing the shortIo call to fail (e.g. pointing `THIRD_PARTY_SERVICE_BASE_URL` at an unreachable host in a local/dev run) and confirming the email/link still renders a working (long) URL, or reproducing the original failure in the DEV tenant and confirming the same request now produces a clickable link — not done from this session (no environment access to trigger a real send).

## Still open
The stray "{ }" near the brand logo in the same reported email is unrelated to this fix and remains unexplained — needs the live template's raw source HTML to investigate (not obtainable without DB/admin-session access). Separately recommended clicking "Reset Template" on this tenant's `meeting-requested` row in the admin UI (confirmed via `sc-saas-admin/modules/developer/email_management.php`'s `resetDefaultTemplate` action that this overwrites `template_content` with the stored `default_template_content`, which should not carry the stray artifact) — not yet confirmed whether this resolved it.

## Note on this fix's rollout
The first attempt at this fix (applied earlier in the same session) was lost from the working tree before being committed — around the same time, a separate, deliberate edit (reverting the `meeting-requested` template's "View Details" href from `reschedule_link` back to `meeting_link`, see [[SAN-853]]) was committed as `sc-saas-backend@b7f89db2` without this fix included. Re-verified the fix was genuinely absent from disk (`git diff` showed nothing, matching the pre-fix version byte-for-byte) before reapplying it and committing separately as `72d1e346`.

## Verification (safety check requested before push)
Before pushing, explicitly verified the fallback change can't regress anything:
- All ~30 call sites of `createShortLink()` — none branch on a falsy/undefined `shortUrl`.
- Every `shortProfileLink` storage column (`startup`, `investor`, `mentor`, `corporate`, `partner`, `individual`, `service_provider`, `program-office-member` entities) is an unbounded `text` column, not a length-limited `varchar` — no truncation risk from a longer fallback URL.
- WhatsApp messages use a separate `whatsappUrl`/`resourceUrl` field, never `shortUrl` — unaffected.
- `npx tsc --noEmit` clean both before and after reapplying.
- `npx eslint` flagged ~480 pre-existing Windows CRLF line-ending issues across the entire file — confirmed present before this change too (not a regression), left untouched as out of scope for this fix.

## Related
[[SAN-853]] — the shortCodes/href consistency fix for the same template, confirmed unrelated to this bug during investigation.
