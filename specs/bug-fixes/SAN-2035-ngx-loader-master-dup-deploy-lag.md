---
id: SAN-2035
title: "ngx-ui-loader master duplicated on /resources: deploy lag, every event on a stale release"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2035
sentry: [SC-SAAS-FRONTEND-EP]
repos: [frontend]
related: [SAN-548, SAN-920, SAN-1993]
commit: none — no code defect, see Investigation
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2035: EP is deploy lag

## Investigation
* 15 events from 10 users. The latest, on 2026-10-22, is on `33244b02e` (Sep 19 build) in prod at `sineedge.sineiitb.org/resources`, thrown from the resources-module chunk template.
* Over 90 days every event is on a stale release (`51eb6706`, `dab63831`, `33244b02e`, `022eafd6`). None is on the current prod build `218edca78`.
* `/resources`: the bare `<ngx-ui-loader>` in `resource-viewer-modal.component.html:1` is still in prod (`git grep` at `218edca78`). SAN-1993 removed it on the branch (`335b4000b` / `a4b905e10`).
* The other URLs are covered by fixes already in prod, SAN-548 and SAN-920 (`49ee4426f`):
  * programs/applied profile-form
  * partners custom-forms additional-information
  * startups/dashboard

## Root cause
Tenants serving old builds.

## Fix
None in code. The `loader-floor.json` gate already tracks bare loaders.

## Blast radius / existing-flow impact
None.

## Verification
The release checks above.

## Ops follow-ups
Deploy HEAD and redeploy the stale tenants: sineedge, trise, firstwings, ciicies, isba and acicvgu.
