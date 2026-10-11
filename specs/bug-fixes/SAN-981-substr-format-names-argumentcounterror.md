---
id: SAN-981
title: "substr() ArgumentCountError — format_names() isn't a truncation helper"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-981
sentry: [SC-SAAS-ADMIN-T]
repos: [admin]
commit: sc-saas-admin@<pending, branch ai_native_setup_aman>
created: 2026-09-24
updated: 2026-09-24
---

# SAN-981 — substr() ArgumentCountError

## Root cause
`themes/default/html/growth_metrics/list.php:634`:
```php
echo (strlen($startupName) > 60) ? substr(format_names($startupName, 0, 60)) . '...' : format_names($startupName);
```
`format_names($value)` (`includes/core_functions.php:1015`) takes exactly one argument (splits on underscores, title-cases) — it is not a truncation helper. The `0, 60` args passed to it were silently ignored by PHP (extra args to a function are dropped, not an error), and the outer `substr(...)` call was left with no start/length arguments of its own, which PHP 8 rejects with `ArgumentCountError: substr() expects at least 2 arguments, 1 given`. The surrounding ternary's own `strlen($startupName) > 60` check makes the original intent clear: truncate the raw name to 60 chars + ellipsis when it's long.

## Fix
```php
echo (strlen($startupName) > 60) ? substr($startupName, 0, 60) . '...' : format_names($startupName);
```

## Blast radius
Single template file, single line. Startup names over 60 chars in the growth-metrics defaulters list now actually truncate (previously fatal-erroring the whole page instead).

## Verification
`php -l` clean.

## Rollout
Sentry issue SC-SAAS-ADMIN-T marked resolved. Not committed/pushed — sitting on `ai_native_setup_aman`, pending review.

## Open questions
None.
