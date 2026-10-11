---
id: SAN-585
title: "WhatsappService.sendMessages crashes if messageData is null/undefined"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-585
sentry:
  - SC-SAAS-BACKEND-17
repos: [backend]
commit: sc-saas-backend@c90d2318
created: 2026-09-02
updated: 2026-09-03
---

# SAN-585 — WhatsappService.sendMessages defensive guard

## Root cause — thin signal, not conclusively confirmed

Single Sentry event, culprit resolved only to `<anonymous>`, no confirmed line number.
`whatsapp.service.ts:52` (`sendMessages`) does `messageData.map(...)` on a parameter typed
`WhatsappDataType[]` with no runtime null-check — the most plausible candidate given the shape of
the crash, but not confirmed as the exact site.

## Fix

`messageData.map(...)` → `(messageData ?? []).map(...)`. Cheap, safe regardless of whether this was
the exact original crash site.

## Blast radius

None.

## Verification

`tsc --noEmit` clean.

## Rollout

Committed `c90d2318`, originally pushed to `ai_native_setup`, also present on `ai_native_setup_aman`
via merge.
