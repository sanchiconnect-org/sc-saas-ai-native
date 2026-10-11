---
id: SAN-860
title: Tripura government Recognition Number on Certificate + Grant Release Letter
type: feature
status: in-review
linear: https://linear.app/sanchiconnect/issue/SAN-860
owner: vishali.k@sanchiconnect.com
repos: [admin, backend]
contracts:
  api: []
  flags: []
  events: []
tenant_scoped: true
depends_on: [SAN-747, SAN-748, SAN-749, SAN-786, SAN-787]
created: 2026-09-21
---

# Tripura government Recognition Number

## Problem

The Directorate of Information Technology, Govt. of Tripura issues its own official per-startup
"Recognition Number" (format `Rec-{year}-{month}-{serial, min 3 digits}`, e.g. `Rec-2026-7-060`, confirmed
against the client's own reference Recognition Certificate and Grant Release Letter PDFs). Neither of the two
places this needs to appear currently uses it:

- The Recognition Certificate's "Cer No:" is `certificates.number`, a plain UUID (traced: the backend's
  `generateNewCertificate()`/`uuidv4()` is dead code, never called — the real number is built entirely in
  `sc-saas-admin/modules/certificates/list.php`'s `generateCertificate` action as `{prefix}{YYYYMMDD}{startup id}`).
- The Grant Release Letter's "Recognition No-" is `startups.recognition_id` — the unrelated, configurable-format
  Startup Recognition ID module (SAN-253), e.g. `TR26-GOM-UDPR-000326`. This was explicitly flagged as interim
  in SAN-786/787's own spec ("Open questions ... this will bind later").

The client has also already manually allotted numbers to ~70 existing startups outside the system, before this
feature existed.

## Resolved scope decisions (2026-09-21, confirmed with the user, not invented)

- **Numbering:** one continuously-incrementing GLOBAL counter. It never resets by month or year — the
  year/month embedded in the string only record *when* a given number was allotted, not a reset boundary.
- **Backfill:** the ~70 legacy startups are entered one-by-one via the new admin edit field on the startup
  detail page. No bulk-import tool.
- **Generation trigger:** lazy and idempotent — allotted automatically the first time *either* the certificate
  or the grant letter is generated for a startup (whichever happens first); both read/write the same value.
  No separate manual "Generate" button (unlike the Startup Recognition ID module, which has one).
- **Scope:** all read/write logic lives entirely in `sc-saas-admin` (traced end-to-end before implementing —
  both the certificate number and the grant letter's recognition number are already 100% generated locally in
  this repo). `sc-saas-backend` is touched ONLY to register the new columns/table as TypeORM entities so
  `synchronize: true` creates the schema on next boot (see Database schema below) — added after the user
  pointed out this repo's own established schema-via-synchronize precedent, superseding the originally-planned
  manual SQL migration. No frontend involvement at all.

## Acceptance criteria

- [x] `startups.tripura_recognition_no` (+ `tripura_recognition_no_generated_at`) columns exist.
- [x] A dedicated, atomically-incrementing `tripura_recognition_no_sequence` table backs the counter — same
      proven `INSERT/UPDATE ... LAST_INSERT_ID()` idiom as the existing `srIdGetNextSerial()`, not `SELECT MAX()+1`.
- [x] The sequence seeds itself once, on first use, from `MAX()` of any already-backfilled
      `tripura_recognition_no` values — so auto-generation continues correctly from wherever the manually
      backfilled 70 leave off, without colliding.
- [x] A Tripura-themed startup's certificate `number` is the Recognition Number, not the generic
      `{prefix}{YYYYMMDD}{id}` format; every other theme/stakeholder type is unchanged.
- [x] The Grant Release Letter's `{{recognition_no}}` resolves via the same idempotent generator.
- [x] Startup detail page shows the Recognition Number directly below the existing Startup Recognition ID
      field, with the same view/edit toggle UI, gated on `tripura_certificate_theme_enabled` and the same
      `srIdCheckRole()` role gate as the existing field.
- [x] Manual edit checks for a collision with another startup's Recognition Number before saving (same pattern
      as `updateStartupRecognitionId`).

## Per-repo plan

### admin (sc-saas-admin)

- `includes/tripura_recognition_no_functions.php` (new) — `tripuraRecognitionNoParseSerial()`,
  `tripuraRecognitionNoPadSerial()`, `tripuraRecognitionNoFormat()`, `tripuraRecognitionNoGetNextSerial()` (the
  atomic counter, with one-time seeding), `tripuraRecognitionNoGenerateIfMissing()` (the shared idempotent
  entry point every consumer calls).
- `modules/certificates/list.php` — in the `generateCertificate` action's per-startup loop, when
  `getCertificateSetting('startup', 'theme') === 'tripura'`, use `tripuraRecognitionNoGenerateIfMissing()` for
  `certificateNumber` instead of the generic prefix/date/id format.
- `modules/application-submission-detail.php` — `$startup` query now also selects `id`; `$recognitionNo` now
  resolves via `tripuraRecognitionNoGenerateIfMissing($database, $startup['id'])` instead of
  `$startup['recognition_id']`. `$recognitionDate` is unchanged (`recognition_generated_at` — the original
  startup-recognition date, matching the reference letter's "Dated-13/07/2026" lining up with the certificate's
  own Issue Dt., not the date this specific number was allotted).
- `themes/default/html/startup-detail/startup-detail.php` — new view/edit block directly below the existing
  Startup Recognition ID block, same two-state pattern (`#tripuraRecNoViewMode`/`#tripuraRecNoEditMode` etc.),
  new JS IIFE mirroring the existing Recognition ID one exactly.
- `modules/startup-detail.php` — new `updateTripuraRecognitionNo` POST handler: role gate, empty check,
  collision check, save + `createAdminLogs()`.
- **Third write path (found 2026-09-22 via screenshots, not in the original design pass):** the per-startup
  "Certificate Number" field on the Startup / MSME Settings tab (`submitAction: createUpdateCertficate` in
  `modules/startup-detail.php`) is a separate, pre-existing way to set `certificates.number`, independent of
  the bulk "Generate Certificate" action. On a Tripura-themed tenant: the template
  (`themes/default/html/startup-detail/startup-detail.php`) now displays the startup's `tripura_recognition_no`
  read-only (prefix stripped, since the fixed prefix box already shows it) instead of the generic/free-text
  value — and deliberately does NOT fall back to a stale `certificates.number` when `tripura_recognition_no`
  isn't set yet, to avoid showing a value Save is about to discard. The `createUpdateCertficate` handler ignores
  whatever was posted and always resolves via `tripuraRecognitionNoGenerateIfMissing()`, and skips the
  "Certificate Number is required" validation (client- and server-side) since an empty value is expected and
  correct pre-generation.

### backend (sc-saas-backend) — schema only

- `src/modules/startup/entities/startup.entity.ts` — added `tripuraRecognitionNo` (`tripura_recognition_no`,
  varchar, nullable, unique) and `tripuraRecognitionNoGeneratedAt` (`tripura_recognition_no_generated_at`,
  timestamp, nullable) alongside the existing `recognitionId`/`recognitionGeneratedAt` columns.
- `src/modules/startup-recognition-id/entities/tripura-recognition-no-sequence.entity.ts` (new) — single
  fixed-row (`id = 1`) counter table, registered in `startup-recognition-id.module.ts` purely for schema
  (`synchronize: true`), mirroring that module's own documented precedent for `DigitalIdCardTemplateEntity`
  etc. — nothing in this NestJS app reads or writes either the new columns or this table; `sc-saas-admin` owns
  them end-to-end via its own Medoo connection to the same tenant DB.

## Database schema

No manual SQL needed — `sc-saas-backend` runs with `synchronize: true` in every environment (confirmed:
`src/core/database/database.module.ts:32`), so registering the entities above is sufficient. The
`startups.tripura_recognition_no`/`tripura_recognition_no_generated_at` columns and the
`tripura_recognition_no_sequence` table are created automatically the next time `sc-saas-backend` restarts for
a given tenant. Deploy/restart the backend for the Tripura tenant before relying on the new `sc-saas-admin` code
paths (certificate generation, grant letter generation, and the new startup-detail edit field all assume these
already exist).

## Addendum (2026-09-22) — stale `certificates.number` on the public certificate view

Found via screenshots: a startup whose `certificates` row predates this feature (or hasn't been re-saved
through any of the three sc-saas-admin write paths since) could show a completely different, stale `number` on
the actual downloaded public certificate than what its `tripura_recognition_no` field correctly showed on the
Information tab — the stored `certificates.number` and `startups.tripura_recognition_no` can drift independently
since only an active admin action re-syncs the former.

**Fix (sc-saas-backend, not admin):** `CertificatesService.getUserCertificates()` — the method backing
`GET /api/v1/certificates`, which `sc-saas-frontend`'s certificate view actually calls — now resolves a startup
certificate's `number` from `StartupEntity.tripuraRecognitionNo` at READ time via a new
`Feature.TRIPURA_CERTIFICATE_THEME_ENABLED` enum entry (backed by the same `tripura_certificate_theme_enabled`
cockpit flag, already reachable in this app's `saasFeatures` from SAN-845, just never given a named enum entry
before), instead of trusting the separately-stored `certificates.number`. Read-only override, never written
back to the row — `tripura_recognition_no` becomes the single source of truth end-to-end; the stored
`certificates.number` value is now vestigial for Tripura tenants. `CertificatesModule` gained `StartupRepository`
as a provider (mirrors the exact pattern `startup-recognition-id.module.ts` already uses) to look up the
startup; `AuditedUpdateService` (that repository's own dependency) needs no explicit import since
`AuditLogModule` is `@Global()`.

Every non-Tripura tenant, and every non-startup/non-profile certificate type, is byte-identical to before.

Committed and pushed to `ai_native_setup`: `sc-saas-backend@c1855c15`.

## Addendum (2026-09-22, same day) — QR/verify lookup broke as a direct consequence

`GET /api/v1/certificates/verify/:certificateNumber` (the public "verify this certificate" page, e.g. from a
scanned QR code) does its own independent lookup — `getCertificateByNumber()`, a plain
`WHERE number = :number` against `certificates`. Once the read-time override above made the DISPLAYED number
diverge from what's actually stored there, verifying by the printed/QR Recognition Number 404'd.

**Fix:** `CertificatesService.verifyCertificate()` now falls back to resolving the startup by
`tripuraRecognitionNo` (new `StartupRepository.getByTripuraRecognitionNo()`, a lean lookup mirroring the
existing `getByRecognitionId()` used by the OTHER Startup Recognition ID module's own public verify flow) when
the plain by-number lookup misses and the Tripura flag is on, loads that startup's certificate the same way
`getUserCertificates()` does, and stamps the same override on it. `tsc --noEmit` and `eslint` clean.

Committed and pushed to `ai_native_setup`: `sc-saas-backend@f6d0ad55`.

## Contracts & invariants

- **No new flag** — reuses the existing `tripura_certificate_theme_enabled` (SAN-845) purely to gate UI
  visibility; the generation logic itself is keyed off the certificate theme setting, not this flag, so a
  tenant that somehow has the theme selected without the flag set still gets correct certificate numbers (the
  flag only controls whether "Tripura" is *offered* in the dropdown, per SAN-847 — it does not gate this
  numbering logic).
- **Tenant scoping (#5):** unaffected — everything here operates through the request's own per-tenant Medoo
  connection, same as every other admin module.
- No API/DTO change, no cross-repo contract touched.

## Test plan

- `php -l` on all touched/new files.
- Extracted and validated the touched `<script>` blocks' JS syntax (PHP tags stripped) via `node --check`.
- No test framework in this repo (per `sc-saas-admin/CLAUDE.md`) — manual QA needed once the SQL migration is
  applied to a dev tenant:
  1. Backfill a test startup's `tripura_recognition_no` via the new edit field, confirm collision check works
     against a second startup.
  2. Generate a certificate for a Tripura-themed startup with no Recognition Number yet — confirm one gets
     allotted and shown as "Cer No:".
  3. Generate/download the Grant Release Letter for the same startup — confirm the SAME number appears as
     "Recognition No-", not a new one.
  4. Confirm a non-Tripura-themed startup's certificate number is unaffected (still the generic format).
  5. Confirm the sequence table seeds correctly: with some startups already holding manually-backfilled
     numbers, the next auto-generated one continues past the highest existing value.

## Rollout

1. Deploy/restart `sc-saas-backend` for the Tripura tenant so `synchronize: true` creates the new columns/table.
2. Deploy this `sc-saas-admin` code.
3. Backfill the ~70 legacy startups' numbers via the new edit field.
4. Spot-check a fresh certificate/letter generation picks up the next number correctly (071+).

## Out of scope

- A bulk-import tool for the legacy backfill (explicitly declined).
- Changing how any OTHER certificate theme's number is generated.
- Any backend or frontend change — confirmed unnecessary by tracing the full generation path before
  implementing.

## Open questions

None blocking. The "Cer No:" the client's certificate PDF actually shows is `RECOGNITION_ID`-shaped for a
tenant that hasn't yet generated a Recognition Number for a given startup — first-time behavior for anyone
downloading a certificate before either document has ever been generated for that startup is: both the
certificate action and the letter action will each independently trigger the same idempotent
`tripuraRecognitionNoGenerateIfMissing()`, so whichever is clicked first wins and the number is identical
either way.
