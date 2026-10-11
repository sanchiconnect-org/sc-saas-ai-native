---
id: SAN-978
title: "implode() TypeError on shortcodes in email_management.php"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-978
sentry: [SC-SAAS-ADMIN-K]
repos: [admin]
commit: sc-saas-admin@<pending, branch ai_native_setup_aman>
created: 2026-09-24
updated: 2026-09-24
---

# SAN-978 — implode() TypeError on shortcodes

## Root cause
`themes/default/html/developer/email_management.php:136` — `implode(", ", $shortCodes)` where `$shortCodes = @json_decode($template['shortcodes'], true)`. `json_decode()` returns `null` on invalid/empty JSON (the `@` suppresses the warning but not the `null` result), and `implode()` requires an array in PHP 8. This whole block is wrapped in an HTML comment (`<!-- ... -->`) — the developer clearly intended to disable it, but PHP still executes embedded `<?php ?>` tags regardless of surrounding HTML comments, so the crash fired anyway.

## Fix
`implode(", ", is_array($shortCodes) ? $shortCodes : [])` — guards against non-array input; behavior for valid JSON arrays is unchanged.

## Blast radius
Single template file, single line. No behavior change for a template with valid `shortcodes` JSON.

## Verification
`php -l` clean. No test suite exists for this repo (per its own CLAUDE.md).

## Rollout
Sentry issue SC-SAAS-ADMIN-K marked resolved. Not committed/pushed — sitting on `ai_native_setup_aman`, pending review.

## Open questions
None.
