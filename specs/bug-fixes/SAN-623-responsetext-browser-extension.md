---
id: SAN-623
title: "Cannot read 'responseText' of null — originates in a browser extension, not app code"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-623
sentry:
  - SC-SAAS-FRONTEND-BT
repos: [frontend]
commit: "none — third-party extension, no app code involved"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-623 — browser-extension XHR wrapper conflict

## Root cause
The full stack trace shows the error originates inside a third-party browser extension's own content
script (`chrome-extension://cjdnfmjmdligcpfcekfmenlhiopehjkd/dist/contentScripts/early-page.js`), which
wraps `XMLHttpRequest` and breaks against our engine.io/socket polling transport. This is the user's
local browser extension interfering with our app's websocket fallback, not a defect in our code.

## Fix
No code fix possible on our side. Recommend closing as won't-fix/external, unless this recurs across
many users (which would suggest our socket transport is unusually fragile against XHR wrappers).

## Verification
Confirmed via full stack trace that the crashing frame is inside the extension's own content script.
