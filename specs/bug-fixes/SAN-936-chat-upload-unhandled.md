---
id: SAN-936
title: Chat file-upload failures crash on messages-file endpoint
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-936
sentry:
  - SC-SAAS-FRONTEND-2W
repos: [frontend]
commit: sc-saas-frontend@14571174 (branch ai_native_setup_vishali, pushed)
created: 2026-09-22
updated: 2026-09-22
---

# SAN-936 — chat-message-form.component.ts unhandled upload errors

## Root cause
`chat-message-form.component.ts` had 4 unguarded `uploadFile`/`uploadFileReply` subscribes across
`handleSelectImage`/`handleSelectFile`. A messages-file 504 (53 users, 160 events) at any of the 4
sites reached Sentry as an unhandled subscribe failure.

## Fix
Converted all 4 sites to `.subscribe({ next: (resp) => {...}, error: () => {} })`, same pattern as
SAN-504.

## Blast radius
None — purely additive error handling, no change to success-path behavior.

## Verification
Re-read the file after editing; confirmed all 4 sites use the same `{next, error}` shape consistently.
No automated test added — step 6 (tests-first) is blocked workspace-wide (no `guardian` skill);
substituted a direct code read.
