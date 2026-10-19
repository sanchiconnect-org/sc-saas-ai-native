---
id: SAN-1929
title: "navigator.clipboard.writeText rejection unhandled in share-links and 5 other copy buttons (SC-SAAS-FRONTEND-HG)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1929
sentry: [SC-SAAS-FRONTEND-HG]
repos: [frontend]
commit: sc-saas-frontend@5548dff24 (branch ai_native_setup_vishali, pushed) — shared/utils/clipboard.util.ts (+ spec) + 6 call sites
created: 2026-10-15
updated: 2026-10-15
---

# SAN-1929: clipboard copy blocked by a permissions policy

## Root cause
* **Sentry:** `Uncaught (in promise): NotAllowedError: Failed to execute 'writeText' on 'Clipboard': The Clipboard API has been blocked because of a permissions policy`.
  * 1 event, community.ginserv.in `/community-feed`, release `218edca78` (current prod).
  * Frame: `share-links.component.ts:40`.
* `navigator.clipboard.writeText` rejects inside iframes or under a permissions policy, and is undefined outside a secure context.
* The codebase had no clipboard helper (no `execCommand('copy')`, `copyToClipboard` or `@angular/cdk/clipboard`).
* All 6 call sites called it unguarded and showed the success toast anyway:
  * awaited, so the rejection was uncaught: `share-links.component.ts:40`, `share-profile-modal.component.ts:74`, `invite-startup.component.ts:81`;
  * not awaited, so the rejection floated: `growth-matrics-share-modal.component.ts:113`, `growth-matrics.component.ts:486`, `pitch-deck-management.component.ts:588`.
* No earlier fix was found in the git log of any of these files.

## Fix
* **New `src/app/shared/utils/clipboard.util.ts`:**
  * `copyToClipboard(text): Promise<boolean>` tries `navigator.clipboard?.writeText` first.
  * If that is missing or rejects, it falls back to a hidden readonly textarea plus `document.execCommand('copy')`.
  * It never throws.
  * Also exports `COPY_FAILED_MESSAGE` ("Couldn't copy the link. Please copy it manually.").
* **All 6 sites** now call the helper:
  * on success they show their original toast, with the same text and type;
  * on failure they show `COPY_FAILED_MESSAGE` as an `'error'` toast, using the toast service already in that file.
* `handlePrint` (share modal), `copyShareLink` and `copyEmbedLink` became `async`. They are only bound to `(click)`, so the return type has no effect.

## Blast radius
Per-site behaviour is otherwise unchanged:
* the `&print=false` suffix stays on both growth-matrics sites;
* invite-startup still only copies when `inviteCode` is set;
* share-profile still copies the url plus the title.

There is no backend or contract impact.

## Verification
* New `clipboard.util.spec.ts`, 5 specs:
  * API succeeds;
  * API blocked (NotAllowedError) and the fallback works;
  * API missing;
  * both paths fail and it returns false;
  * `execCommand` returns false.
* `npx tsc --noEmit -p tsconfig.app.json` and `-p tsconfig.spec.json`: exit 0.
* `npm run gates`: exit 0, 1103/1103 specs (floor 1098).
* **Not tested:** real-browser iframe / permissions-policy behaviour.
