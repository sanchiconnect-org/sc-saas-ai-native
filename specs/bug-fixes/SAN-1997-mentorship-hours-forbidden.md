---
id: SAN-1997
title: "Jobs( Forbidden resource ) on ciicies mentorship-hours (SC-SAAS-FRONTEND-2Y) — handled 403, release predates SAN-471 filter"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1997
sentry: [SC-SAAS-FRONTEND-2Y]
repos: [frontend]
related: [SAN-471, SAN-504, SAN-581, SAN-1041]
commit: none — no code defect, see Investigation
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1997: Jobs( Forbidden resource ) on /mentorship-hours

## Investigation
* **The event:** one event, ciicies `/mentorship-hours`, release `51eb6706` (2026-08-18), Android.
* **Which endpoint 403s:**
  * `/mentorship-hours` loads `TrackerComponent` (`modules/tracker/tracker.component.ts`).
  * `ngOnInit()` → `handleSubscriptions()` always calls `MentorshipService.getMentorShipStats()` (`GET mentorship/stats`) and `getMentorShip()` (`GET mentorship`).
  * It also calls `mentorship/startups` for a mentor and `mentorship/mentors` for a startup.
  * All four warn `Jobs( … )` (`core/service/mentorship.service.ts:35-75`), a copy-paste label.
* **Backend guards** (`sc-saas-backend/src/modules/mentorship/mentorship.controller.ts:61-85`):
  * `stats` and `GET /` need `Role.STARTUP | Role.MENTOR` (RolesGuard) and features `mentors` + `mentor_hours` (FeatureGuard).
  * Both guards return `false`, which Nest turns into `403 Forbidden resource`.
* **Should the page call it for this account?**
  * Every in-app link to `/mentorship-hours` is shown only to STARTUP/MENTOR accounts with `mentor_hours` on: `navMenus.ts:254-263`, `calender/helpers.ts:143-160`, the dashboards, `community-feed-stats`.
  * ciicies has `mentor_hours: true` (public `verify_tenant`, checked 2026-10-22).
  * The `mentors` flag is not in the public response, so whether it is off could not be confirmed.
  * So the 403 is either a non-startup/non-mentor account reaching the URL directly (email `nextUrl=/mentorship-hours`, bookmark, or the `connection-list-view` link), or `mentors` being off on that tenant.
* **What the user gets:**
  * The 403 is not `SKIP_FORBIDDEN_REDIRECT`, so the interceptor toasts and navigates to `/`.
  * The tracker subscribers have no-op error callbacks (SAN-504), so nothing is thrown unhandled.
  * The user lands on home with a "Forbidden resource" toast.
* **The filter:** `src/main.ts` `HANDLED_HTTP_FAULT` drops `( Forbidden resource )`. It was added by SAN-471 `2e1dd4dc7` (2026-08-20), and SAN-471 cited 2Y by name.
  * `git merge-base --is-ancestor 2e1dd4dc7 51eb6706` → **no**.
  * On `origin/main` → yes.

## Fix
None for the Sentry event: deploy lag of an already-filtered expected 403.

## Blast radius / existing-flow impact
None (no change).

## Verification
* Ancestry checks above.
* `curl https://api.tenants.sanchiconnect.com/api/v1/public/global/verify_tenant/startupaffiliation.ciicies.in` → `mentor_hours: True`, no `mentors` key among the 218 features.

## Open (minor, not changed)
* `TrackerComponent.ngOnInit()` calls `handleSubscriptions()` before it checks `brandDetails.features.mentor_hours`, and it never checks account type. So the page fires the requests, and only then redirects to `/errors/404` or gets bounced to `/` by the interceptor.
* A guard (skip the calls unless STARTUP/MENTOR and `mentor_hours`) would avoid the extra 403 and toast.
* **[DESIGN DECISION PENDING]:** what should a non-startup/non-mentor account see at `/mentorship-hours`: 404, home, or a message? Product question. Not implemented.

## Recommended close
Close as deploy lag / expected condition. Ciicies needs a build containing `2e1dd4dc7`.
