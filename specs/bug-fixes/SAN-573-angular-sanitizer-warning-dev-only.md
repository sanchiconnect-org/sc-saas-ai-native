---
id: SAN-573
title: "Angular 'sanitizing HTML stripped some content' warning (SC-SAAS-FRONTEND-46) — dev-mode-only, working as intended, no data loss"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-573
sentry: [SC-SAAS-FRONTEND-46]
repos: [frontend]
related: [SAN-1573, SAN-158, SAN-527]
commit: none. Working as intended; no code change
created: 2026-10-13
updated: 2026-10-13
---

# SAN-573: sanitizer warning on rich-text rendering

## Investigation
* **Dev-mode only.** Angular's `DomSanitizer` logs `WARNING: sanitizing HTML stripped some content` **only when `isDevMode()` is true**. A production build sanitizes just the same, but silently.
* **All 78 events in SC-SAAS-FRONTEND-46 are `environment: local`** (90-day aggregate). They come from dev-mode builds on `thub.sanchidev.in` and its tenant subdomains, plus `localhost:4200`. There are zero production events.
  * SAN-158 already records `thub.sanchidev.in` serving a non-production Angular build.
  * Sentry has the group `ignored` (archived until escalating). The last event was 2026-10-06.
* **Not specific to the investor profile.** The investor profile accounts for only 3 of 78 events. The rest come from pages rendering rich text via `[innerHTML]` (160 bindings in the app): program apply (24), calendar events (19), event register and preview (17), facilities, learning, and individual and mentor profiles.
* **"Possible data loss": no.** Sanitization applies only to **rendering**. The stored HTML is never modified.

## Does legitimate user-authored formatting get stripped? No
* Quill is **1.3.7** (ngx-quill 16.2.1). It writes native `<ul>/<ol>` lists, not Quill 2's `<li data-list>`, which Angular would strip.
* The shared `quillConfig.ts` and every local toolbar (challenge form, community feed form/post, dynamic event-form field) have `color`, `background`, `image` and `video` **disabled**. Our editors therefore cannot produce inline `style` attributes or `<iframe>` embeds, which are the two things Angular strips.
* What our editors can produce is kept by Angular's allowlist: `ql-align-*` classes, links with `target`/`rel`, and headers, lists and bold/italic.
* The stripped content is therefore markup that didn't come from these editors: pasted or imported HTML, or descriptions authored elsewhere (for example, admin-authored program and event text with inline styles). Stripping `style`, `<script>`, event-handler attributes and the like from that content is the sanitizer **doing its job**. Bypassing it on user-authored fields (investor bios, profiles) would open stored XSS.

## Decision
No code change. This is working as intended, per the ticket's own third bullet ("If it is genuinely malicious/malformed markup being stripped, this can be closed as working-as-intended").
* **The Sentry noise belongs to SAN-1573**, which stops Sentry ingesting dev-build warnings at the source. It is assigned to the same owner.
* **Optional product follow-up, not filed:** if admin-authored content such as program or event descriptions must keep inline styling, the decision is to trust that specific admin-only content with the existing `safeHtml` pipe (`bypassSecurityTrustHtml`), field by field. That is a security decision for the dev lead, never a blanket change.

## Verification
* Sentry aggregates by environment, release and URL over 90 days.
* Read the Quill version, the editor toolbars and `pipe.safehtml.ts`. Nothing was modified.
* Contract checks do not apply: there is no flag, API, auth or tenant change.

## Closed 2026-10-13
SAN-573 was closed as Done (working as intended). The dev-build Sentry noise is tracked in SAN-1573. Reopen this if the warning ever appears with `environment: production`, which would mean a dev-mode build is deployed to production, or if a user reports specific formatting missing from content written in our editors.
