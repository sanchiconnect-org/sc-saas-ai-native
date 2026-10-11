---
id: SAN-794
title: "Pitch-file upload 400 left 'Uploading...' stuck and surfaced as an unhandled HttpErrorResponse"
type: bug-fix
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-794
sentry: [SC-SAAS-FRONTEND-72, SC-SAAS-FRONTEND-C6]
related: [SAN-615]
repos: [frontend]
commit: sc-saas-frontend@72c9af6d (branch ai_native_setup_vishali)
created: 2026-09-28
updated: 2026-09-28
---

# SAN-794 — reset the upload state when the pitch-file upload fails

## Root cause
The 400 comes from the backend: `sc-saas-backend` `pitch-deck.controller.ts:119-122` → `verifyFileContentSignature()` returns false ("Uploaded file content does not match its extension"). This is the same root cause as **SAN-615**. Each of the 5 pitch-file 400 events in SC-SAAS-FRONTEND-72 matches, to the second, an SC-SAAS-FRONTEND-C6 warning with that message. Other 400 sources (DTO enum, `documentFileFilter`) were ruled out.

The frontend side effect: `PitchDeckService.uploadPitchFile()` toasts the error and rethrows it. `ElevatorPitchComponent.pitchDeckFileDroppedHandler()` subscribed with a success handler only, so the rethrown error went unhandled (reported to Sentry as 72), and `this.uploading` was never reset. The "Uploading..." badge stayed on screen.

## Fix
`modules/startups/pages/edit/elevator-pitch/elevator-pitch.component.ts`: added an error callback to the `uploadPitchFile().subscribe()` that sets `this.uploading = false`. The toast (already shown by the service) is unchanged.

## Blast radius
`sc-saas-frontend`, one component. No API/DTO change. The success path is untouched.

## Not fixed here
The backend signature check still wrongly rejects legitimate files: password-protected OOXML files are OLE2 containers, and some PDFs have leading bytes before `%PDF`. That needs a `Repo: Backend` ticket (see SAN-615). It was not edited, because this issue is labeled Repo: Frontend.

## Verification
- `tsc -p tsconfig.app.json --noEmit` clean.
- No automated test added. Manual check: upload a file the backend rejects (for example a .txt renamed to .pdf) on Startup edit → Pitch deck. You should see the error toast, and the "Uploading..." badge should clear so you can retry.

## Open questions
None for the frontend. The backend ticket for the signature check is still pending the user's go-ahead.
