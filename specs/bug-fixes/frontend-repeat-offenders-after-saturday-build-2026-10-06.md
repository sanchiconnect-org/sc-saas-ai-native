# Frontend Sentry — what still fires after the Saturday build (2026-10-06)

Source: Sentry project `sc-saas-frontend`, `environment:production`, queried 2026-10-06 ~05:30 UTC.

## The "Saturday build"
`sc-saas-frontend@bcf88383d` = merge of PR #1902, 2026-10-02 21:31 IST (first events 2026-10-02 17:22 UTC). It is by far the dominant release in the last 4 days (402 of ~620 events). It
contains the August/early-September filters (SAN-471 `2e1dd4dc7`, SAN-599/601/608 `4e4bd3cb4`) but **none of the 5-6 Oct fixes** (SAN-1660..1669, SAN-1673, `6638635f2`, `4508cc760`, `8dad09952`,
`e5280e7f2`, `320caa25b` and others are not ancestors of it). So an issue that fires on `bcf88383d` and is fixed only by a 5-6 Oct commit is expected; one that fired on it although its fix is in the build is a real repeat offender.

## A. Still firing on the Saturday build (402 events)

| Issue | Events | What it is | Domains (events) | Status |
|---|---|---|---|---|
| SC-SAAS-FRONTEND-26 | ~348 (about 85%) | `Tenant verification failed: resolve-domain/<host>` (504 or status 0 from `api.tenants.sanchiconnect.com`; 5 are `Direct access is not allowed`) | sg.sanchiapp.com 186; connect.iiitdic.in 49; supernova.gdai.in 35; ecosystem.firstwingsconnect.com 22; acceleration.ihubgujarat.in 11; hub.startupsingam.com 11; sineedge.sineiitb.org 8; ihub.sanchiconnect.com 6; connect.trise.tripura.gov.in 4; start.runwayincubator.com 4; ecosystem.ihubup.com 3; community.ginserv.in, startupaffiliation.ciicies.in, nasscom.sanchiconnect.com, a bare IP 1 each | Open. Server-side: tenants cache SAN-557 (`f74d37d`) not deployed. By design a fatal outage alert (SAN-159). Client: SAN-1672 added a bounded retry for a transient fault (see its record, which holds the same domain evidence); stale-if-error is not implemented. |
| SC-SAAS-FRONTEND-2J | ~25 | Unhandled `Http failure response ...` (a catch-all group): 401 on `dashboards/user`, `connections`, `connections/requests/received`, `community-wall/posts/me/stats`; 404 on the same plus `application-programs-management/.../apply`; 400 on chat `mark-read` | connect.trise.tripura.gov.in, api-nemecosystem.massentrepreneurship.org, supernova.gdai.in, ecosystem.firstwingsconnect.com, connect.iiitdic.in, community.ginserv.in | 401s: SAN-1673 (this change). mark-read 400: SAN-1665. 404s: open (1 user, all endpoints 404 in the same second: a tenant routing problem, not a handler). |
| SC-SAAS-FRONTEND-11 | 7 (3 users) | `[ngx-ui-loader] loaderId "master" does not exist` | not captured in the aggregate | Open. Same family as the "master is duplicated" cluster (SC-SAAS-FRONTEND-EP, SAN-1623); needs the loader refactor. |
| SC-SAAS-FRONTEND-35 | 7 (7 users) | `Error invoking postMessage: Java object is gone` (in-app browser) | n/a | SAN-1668 filter (not in the build). |
| SC-SAAS-FRONTEND-GR | 3 | `#pageLoader` selector | n/a | SAN-1666 (not in the build). |
| SC-SAAS-FRONTEND-GK | 4 (1 user) | `getIndividualInvestorCompleteness( Individual not found )` | connect.trise.tripura.gov.in | Open: expected "profile missing" message, not in the filter, user-facing display unverified. |
| 2W / 1 / 7T / GN / F2 / 6S / FB / 4C | 1-2 each | unhandled 504 / status 0, upload "Unexpected end of form", investor-form validation text, 504s | runway, trise, ihub | FB / 4C / 6S: fixed 6 Oct (not in build); the rest open. |

## B. Domains still seen on OLDER releases after 3 Oct (not the Saturday build)

A host that appears here either was not redeployed or has clients on a stale cached PWA (service worker). Sentry cannot tell which; a host with only old releases below is the strongest candidate for "not redeployed".

| Host | Older releases seen (events) |
|---|---|
| connect.acicvgu.com | 022eafd6 = 2026-07-31 (8) only |
| trise.tripura.gov.in (bare host) | 022eafd6 = 2026-07-31 (16), 6410c46b (3) only |
| program.siicincubator.com | 046862a8 (2) only |
| connect.trise.tripura.gov.in | dab63831 = 09-03 (8), 9dde12280 = 09-25 (12), 51eb6706 = 08-18 (1) (also on bcf88383d) |
| ecosystem.firstwingsconnect.com | 9dde12280 (11), dab63831 (5), 90bde7be0 = 09-14 (3), 33244b02e = 09-19 (3) (also on bcf88383d) |
| supernova.gdai.in | 90bde7be0 (2), dab63831 (2), 9dde12280 (1), 33244b02e (1) (also on bcf88383d) |
| connect.iiitdic.in | 90bde7be0 (6), 9dde12280 (2), 33244b02e (3) (also on bcf88383d) |
| app.sanchiconnect.com | e267a0303 = 10-01 stagingdemo (14) (also on bcf88383d) |
| hub.startupsingam.com, hub.isba.in, start.runwayincubator.com, community.ginserv.in, sineedge.sineiitb.org | 9dde12280 / 90bde7be0 / 33244b02e (1-3 each) |

Conclusion: the Saturday build is NOT on every domain. At least three hosts show only 2-month-old or older builds, and several others still have clients on builds from September, which points to
the stale-PWA problem (SAN-1140) as well as un-redeployed tenants. Every fix that is not in `bcf88383d` also needs a redeploy of each tenant's frontend.

## C. What this change set did
- SAN-1673: drop the unhandled 401 re-report (the interceptor already handled the session).
- Module specs updated for the modules touched this week (see the module.spec.md bullets for SAN-1660/1662/1663/1664/1665/1666/1667/1668/1669/1673).

## D. Decision still needed
FRONTEND-26: serve the randDetails already cached in localStorage when esolve-domain keeps failing after the SAN-1672 retry (stale-if-error). It keeps returning visitors online through an outage but can serve stale feature flags or maintenance mode, so it needs the product owner and dev lead. Also open: a global bounded retry for idempotent GETs (the long tail behind SC-SAAS-FRONTEND-2W and -1, about 40 endpoints with 1-2 events each, one user's burst of unrelated 504s in the same second), which has the same load trade-off.
