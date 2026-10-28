# SAN-1623 — ngx-ui-loader duplicate "master" loaderId: bare-loader floor in CI

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1623 · **Repo:** sc-saas-frontend
- **Earlier rounds of the same defect:** SAN-129, 130, 139, 157, 372, 383, 433; SAN-920 (Hire page, `49ee4426f`)
- **Sentry:** crash groups SC-SAAS-FRONTEND-EP, GT, H7 (`loaderId "master" is duplicated`, level error); FRONTEND-11 (`loaderId "master" does not exist`, level warning, already ignored)

## Root cause
A `<ngx-ui-loader>` without a `loaderId` claims the library's default id `master`. When two are bound at the
same time (a page and a shared component inside it, or a page and a modal), `bindLoaderData()` throws
`loaderId "master" is duplicated` and the view crashes.

On 2026-10-15 there were **91** live bare loaders in the templates (106 counting commented-out markup), in 91 files.
Six of those files are shared components, which are the clash sources because they are placed inside pages
that already have their own master loader.

`does not exist` (FRONTEND-11, about 857 production events in 30 days) is a different, harmless case: code calls
`ngxService.start()/stop()` while no master loader is on screen. The library only `console.warn`s. It is Sentry noise
(SAN-1573), not a crash.

## Evidence that no new clash is open
The most recent production "is duplicated" event (H7, 2026-10-11, `hub.startupsingam.com/jobs`) came from release
`bcf88383d` (2026-10-02), which does **not** contain the SAN-920 fix `49ee4426f`. EP (last 2026-10-08) and GT
(2026-10-05) also predate the fix reaching every tenant. No event has been seen from a build that includes it.

## Fix (phase 1 — no runtime change)
- `scripts/loader-floor.js`: counts bare `<ngx-ui-loader>` opening tags under `src/**/*.html` (multi-line tags
  included, HTML comments stripped). `check` fails above the floor and names the file(s) that gained one;
  `lower` writes a lower count back and refuses to raise it.
- `loader-floor.json`: floor of 91, with the per-file counts.
- `scripts/gates.sh`: new required gate `loader-floor`; `.github/workflows/ci.yml` runs it with the build step.
- `.github/CODEOWNERS`: the floor file and script need the same reviewers as the test floors.

Lowering is manual (`node scripts/loader-floor.js lower`); the check prints that hint when the count falls.

## Phase 2 (2026-10-21): own loaderId where the component drives its own loader
Three shared components start and stop their own loader. They now use a named loader instead of `master`:
- `change-profile-type-modal` (`change-profile-type-loader`). Opened from the profile menu over any page, so it clashed with that page's bare loader.
- `book-facilitys` (`book-facilitys-loader`). Embedded in `facility-details`, which has no loader of its own.
- `book-facility` (`book-facility-loader`). Currently not used anywhere.

Each has `start()`/`stop()` → `startLoader(id)`/`stopLoader(id)`. The floor went from 91 to 88.

Left as they are, on purpose: `dashboard-common-calender` and `supporting-documents`. They never start a loader themselves; their bare loader is the only `master` display on most dashboard pages (no page-level loader there), so renaming it would remove those pages' spinners. `dashboard-common-calender` already has the SAN-920 `renderLoader` switch for pages that do have their own loader. A bulk rename of the rest stays unsafe, because modals rely on the shared master loader.

## Verification
No automated test framework covers build scripts; verified by running it:
- `bash scripts/gates.sh loader-floor` → `91 bare loaders, at the floor`, exit 0.
- Added a probe template with one bare multi-line loader, one named loader and one commented-out loader → check
  exit 1, names only the probe file (`1 (was 0)`); `lower` refuses to raise (exit 1). Probe removed.
- Floor set to 92 → check passes with the `lower` hint; `lower` writes 92 → 91.

## Closing criteria still open
Sentry quiet for 30 days on "is duplicated"; the seven earlier issues closed with this evidence.
