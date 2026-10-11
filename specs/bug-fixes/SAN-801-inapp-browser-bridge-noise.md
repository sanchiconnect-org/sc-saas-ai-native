---
id: SAN-801
title: "In-app-browser bridge postMessage error (Android) — browser bridge noise, no code defect"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-801
sentry:
  - SC-SAAS-FRONTEND-3Y
repos: [frontend]
commit: "none — not a code defect"
created: 2026-09-23
updated: 2026-09-23
---

# SAN-801 — Android in-app-browser bridge teardown race

## Root cause
Not a code defect — an Android in-app-browser bridge quirk (the native WebView bridge object has
already been torn down by the OS/host app by the time a queued `postMessage` call fires). Matches the
non-actionable pattern already filed and closed as noise across SAN-197–204 (all Done, "in-app-browser
bridge noise, not application code"). This specific bridge channel
(`navigation_performance_logger_android`) hadn't been filed individually before, but the failure mode
and mechanism are identical.

## Fix
No code change — fires from the native bridge layer outside the Angular app's control. Consider a
Sentry inbound filter for `iabjs://` culprits if this or sibling bridge channels keep generating
low-value alerts.

## Related
SAN-197–204 (same failure class, same conclusion).

## Verification
Matched against the established SAN-197–204 precedent for this exact failure mode.
