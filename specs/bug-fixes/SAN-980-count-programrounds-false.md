---
id: SAN-980
title: "count() TypeError on programRounds — false from a failed/empty query"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-980
sentry: [SC-SAAS-ADMIN-B]
repos: [admin]
commit: sc-saas-admin@<pending, branch ai_native_setup_aman>
created: 2026-09-24
updated: 2026-09-24
---

# SAN-980 — count() TypeError on programRounds

## Root cause
`themes/default/html/startup-detail/startup-detail-printable.php:1525` — `count($this->programRounds) > 0` where `$this->programRounds` can resolve to `false` (a Medoo query result, not guaranteed to be an array on a query error or unset property).

## Fix
`is_array($this->programRounds) && count($this->programRounds) > 0` — short-circuits before `count()` runs on a non-array.

## Blast radius
Single template file, single line. No behavior change when `programRounds` is a real array.

## Verification
`php -l` clean.

## Rollout
Sentry issue SC-SAAS-ADMIN-B marked resolved. Not committed/pushed — sitting on `ai_native_setup_aman`, pending review.

## Open questions
None.
