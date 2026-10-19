---
id: SAN-000                     # Linear id — also the branch prefix (<id>-<slug>)
title: <one-line title>
type: feature
status: draft                   # draft → approved → in-progress → in-review → done
linear: <https://linear.app/...>   # the EXISTING project the spec lives in (default: Enhancement)
linear_milestone: <SAN-000 — title>  # the spec's milestone in that project (SAN-1579); its issues sit here
owner: <name@sanchiconnect.com>
repos: []                       # subset of [tenants, backend, frontend, admin, ai-startups-analyzer, sc-saas-3rdparty-webservices, sanchiconnect-saas-tenants-admin] — DEPENDENCY ORDER
contracts:
  api: []                       # backend routes added/changed, e.g. "POST api/v1/foo/bar"
  flags: []                     # snake_case flag names touched
  events: []                    # domain events emitted/consumed
tenant_scoped: false            # true if any tenant-scoped data is read or written
depends_on: []                  # other spec ids that must be `done` first
created: 2026-06-17
---

# <title>

## Problem
<What's broken or missing, and for whom. Why now. Keep it to a few sentences.>

## Acceptance criteria
<Testable, checkable outcomes. All must pass for `done`.>
- [ ] ...
- [ ] ...

## Per-repo plan
<One heading per repo in `repos`, in dependency order (tenants → backend → frontend → admin).
Omit repos not touched. Cite real files/modules.>

### tenants
- ...

### backend
- ...

### frontend
- ...

### admin
- ...

## Contracts & invariants
<Spell out each item in `contracts`. Then state which of the 6 workspace invariants this touches
(flag names / API contract / verification shape / auth / tenant scoping / cross-workspace PowerPitch contract) and how it stays safe.>
- **Flags:** ...
- **API:** ...
- **Events:** ...
- **Invariants at risk:** ...

## Test plan
<Per repo: jest / karma / php -l / manual. Plus the cross-repo smoke check.>
- tenants: ...
- backend: ...
- frontend: ...
- admin: ...
- cross-repo: ...

## Rollout
<Deploy-safe sequencing across independently-deployed repos. Flag default-off first, enable last.
Migrations and their backward-compatibility. Feature-flag gating.>

## Out of scope
<What this spec explicitly does NOT do.>

## Open questions
<Anything unresolved. A NON-EMPTY list means this spec is NOT approvable — resolve or move to Out of scope first.>
- ...
