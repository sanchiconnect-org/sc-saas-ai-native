---
id: SAN-678
title: "Error restoring session i: Failed to connect to MetaMask — browser extension noise, no web3 integration exists"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-678
sentry:
  - SC-SAAS-FRONTEND-4H
repos: [frontend]
commit: "none — no code path exists to fix"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-678 — browser-extension-injected error, no app code involved

## Root cause
Grepped `MetaMask|ethereum|web3` across `sc-saas-frontend/src` — no genuine Web3/wallet integration
exists (only unrelated font-glyph asset filenames, e.g. `la-brands-400.svg`, a false positive on
"brands"). This app has no MetaMask code path at all.

## Fix
No fix possible in this repo — originates from a browser extension (MetaMask or similar) injecting
itself into the page uninvited.

## Verification
Grepped the full frontend source tree for any MetaMask/web3/ethereum reference; found none relevant.
