---
id: SAN-968
title: "Broadcast Messages Details page fatals on non-string ses_email_queue.response"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-968
repos: [admin]
commit: sc-saas-admin@501f8594
created: 2026-09-23
updated: 2026-09-23
---

# SAN-968 — Broadcast Messages Details page crash on non-string response

## Request

`modules/broadcast_messages/details.php` threw an uncaught fatal error — `TypeError: trim(): Argument #1
($string) must be of type string, array given` at line 325 — making the entire Details page inaccessible for
at least one broadcast.

## Root cause

`ses_email_queue.response` is written from `sc-saas-backend`'s untyped `response: any` field
(`ses-email.service.ts`), so its shape isn't guaranteed to be the plain SMTP string (`"250 Ok <messageId>"`)
this page's MessageId-extraction code assumed unconditionally. For at least one row it came back as an
array/object instead, and `trim()` on that array crashed the whole page.

## Fix

Added an `is_string($response['response'])` check alongside the existing empty-response skip — a non-string
response value now just leaves that row's `messageId` blank instead of fataling the page.

## Verification

`php -l` clean. This is a defensive fix on the admin (consumer) side; the backend's underlying `response: any`
typing was not narrowed as part of this fix — that would be a separate, larger investigation into why that
specific send path returns a different shape.

## Rollout

Committed and pushed to `ai_native_setup`: `sc-saas-admin@501f8594`.

## Open questions

None blocking — the backend's `response: any` typing narrowing is explicitly out of scope for this defensive
consumer-side fix (see Verification).
