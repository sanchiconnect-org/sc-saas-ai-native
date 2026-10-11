---
id: SAN-1042
title: "Certificate signature image 404 — no fallback"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1042
sentry: [SC-SAAS-FRONTEND-G6]
repos: [frontend]
assignee: Mahima Sharma
commit: sc-saas-frontend@<uncommitted — branch ai_native_setup_mahima, awaiting Mahima's verification>
created: 2026-09-28
updated: 2026-09-28
---

# SAN-1042: Certificate signature image 404 — no fallback

## Classification
ENV_ERROR (missing tenant asset) + small CODE_ERROR

## Root cause
The tenant setting's `certificate_person_signature-*.jpg` no longer exists on ImageKit, which is a data issue. The message comes from `html-to-image` (`Resource "..." not found`), which already substitutes a placeholder and only calls `console.warn`. The live `<img>` showed a broken-image icon.

## Fix
Added an `(error)` handler to the signature `<img>` in all 7 certificate templates. It swaps the src for an inline transparent GIF, so there's no broken icon, and html-to-image skips `data:` URLs on export. The missing file still needs re-uploading in tenant settings. If an export runs before the image's error event fires, one warn can still get through.

## Files changed
- `src/app/modules/sc-certificate-renderer/{aqua,classic,default,modern,pink,red,tripura}-certificate/*.component.html`

## Verification
`npx tsc -p tsconfig.app.json --noEmit` is clean, and `ng build --configuration development` (AOT, covers the templates) exited 0. No automated regression test has been added yet; one is proposed and waiting for approval. Contract check: frontend-only, and no controller/DTO/flag was touched, so /audit-contract, /trace-flag and /check-isolation don't apply.

## Existing-flow check (no functionality broken)
The `(error)` handler only fires when the image fails to load, so valid signatures render exactly as before. For a failed image the slot is now blank instead of a broken icon. The name-only fallback isn't shown, because `p.signature` is still set.

## 10-step process (SanchiConnect Developer Guide)
1. **Orient:** read the Sentry issue, event details and breadcrumbs. Done.
2. **/from-linear:** the Linear issue was created from Sentry and filed in the *Production Defects* project, assigned to Mahima. Done.
3. **Spec:** narrowly scoped, single-repo fix, so the lightweight `/bug-fix` path was used (this record) instead of a feature spec. Done.
4. **Design questions:** none pending. Data/ops follow-ups (if any) are listed above and not invented here.
5. **Contract check:** frontend-only. No controller, DTO, flag or tenant-scoped query changed, so `/audit-contract`, `/trace-flag` and `/check-isolation` don't apply. Backend code was only read, never edited.
6. **Tests first:** blocked workspace-wide (no guardian skill). As a substitute, `npx tsc -p tsconfig.app.json --noEmit` is clean and the `ng build --configuration development` AOT build exited 0. No automated regression test has been added; one is proposed and waiting for Mahima's go-ahead.
7. **Branch:** the working tree is `sc-saas-frontend` on `ai_native_setup_mahima`. No new branch was created. (CLAUDE.md names `ai_native_setup`; Mahima decides.)
8. **Implement:** done, see Fix.
9. **Verify:** existing-flow check above, bug-fix record written, Linear moved to In Review with a root-cause comment.
10. **Commit/push:** **not done, on purpose.** Waiting for Mahima's manual verification. Linear moves to Done only after that.
