---
id: SAN-1136                    # lowest per-repo issue; full set SAN-1136 (tenants), SAN-1137 (tenants-admin),
                                 # SAN-1138 (backend), SAN-1139 (admin). Project P-SAN-63.
title: ZenxAI Voice Call Billing via AI Credits
type: feature
status: in-review
linear: https://linear.app/sanchiconnect/project/zenxai-voice-calls-for-draft-applications-5fbb3554def5
owner: nirmal.s@sanchiconnect.com
repos: [tenants, sanchiconnect-saas-tenants-admin, backend, admin]
contracts:
  api:
    - "NONE on the sc-saas-backend API contract. The tenants public GET /ai-credits/task-rates gains one row only when an operator creates the ai_voice_call rate (shape unchanged)."
  flags:
    - "zenxai_crm_enabled (existing, SAN-1028)"
    - "ai_credits_enabled (existing, FT-005)"
  events: []
tenant_scoped: true
depends_on: [SAN-1028, FT-005]
created: 2026-09-29
---

# ZenxAI Voice Call Billing via AI Credits

## Problem

SAN-1028 lets tenant admins place ZenxAI AI voice calls, but nothing charges the tenant. Every
call is paid from **Sanchi's own** ZenxAI account, one shared account whose `ZENXAI_API_KEY` is
in the sc-saas-admin `.env`. The product owner decided (2026-09-29) that ZenxAI is a paid
feature for tenants:

- **Access** is by feature flag (`zenxai_crm_enabled`) plus **AI Credits**.
- Sanchi prepays ZenxAI. Tenants buy Sanchi AI Credits and each call consumes them.

## Decisions (product owner, 2026-09-29)

1. **One shared wallet.** Voice calls consume the existing per-tenant AI Credits wallet
   (`ai_credit_wallets`), the same balance as AI analysis. Voice credits are not ring-fenced.
2. **₹ price per credit** is set in tenants-admin → AI Credits → **Packages** (existing, no code
   change). Voice-named packages are optional labelling only.
3. **Credits per minute** is set in tenants-admin → AI Credits → **Task Rates** as the new task type
   `ai_voice_call` (`credits_per_unit` = credits per started minute). Operators can edit it at
   runtime with no deploy.
4. **Non-regression is a hard requirement:** no existing AI Credits, analysis, purchase, or
   ZenxAI flow may change behaviour.

## ZenxAI cost to Sanchi (evidence: ZenxAI "Committed Usage Discount" sheet, supplied 2026-09-29)

Per-minute rates, excluding GST: pay as you go ₹4.50; Starter (₹7,000) ₹4.00; Growth (₹15,000)
₹3.85; Business (₹25,000) ₹3.65; Scale (₹30,000) ₹3.50; Pro (₹75,000) ₹3.25; Enterprise
(₹1,50,000) ₹3.00. Guidance: price tenants against the ₹4.50 pay-as-you-go rate, so any higher
ZenxAI tier only adds margin.

## Code findings (evidence-tagged)

- **[verified: `sc-saas-admin/includes/ai_credits_functions.php`]** Existing helpers, all on
  `$mainDatabase` and keyed by `domain`:
  - `getAiCreditAvailableBalance` (balance − reserved)
  - `getAiCreditTaskRate`
  - `reserveAiCredits($domain, $credits, $sourceRef)`: increments `reserved_balance` and inserts a
    RESERVE row with **no `task_type`**. It does **not** check affordability; callers pre-check.
  - `settleAiCredits(...)`: atomically claims RESERVE→DEBIT, deducts only `WHERE balance >= actual`,
    and hardcodes `source_type = 'ANALYSIS'`.
  - `refundAiCreditReservation`: RESERVE→REFUND claim, idempotent.
  - `reconcileStaleAiCreditReservations($domain, 6)`: refunds **every** RESERVE row older than
    6 h. Its only caller is `modules/ai_credits/overview.php:43`.
- **[verified: `sanchiconnect-saas-tenants/.../ai-credit-task-rate.entity.ts`]** `task_type` is a
  MySQL ENUM (`AiTaskType`: ai_analysis, ai_thesis_generation, ai_rescore, ai_source_refresh).
- **[verified: `.../ai-credit-ledger.entity.ts`]** `source_type` is an ENUM (`AiLedgerSourceType`:
  PURCHASE, ANALYSIS, GRANT, RESERVE, REFUND). `task_type` on the ledger is a free varchar(100).
- **[verified: `sanchiconnect-saas-tenants-admin/modules/ai_credits/task_rates.php:25-39`]** Task
  types are read from the live ENUM via INFORMATION_SCHEMA. A hardcoded fallback list is used only
  when that read fails.
- **[verified: `sc-saas-admin/themes/default/html/ai_credits/{history,overview}.php`]** A RESERVE
  row with an empty `task_type` is displayed as `ai_analysis`. `source_type` is displayed
  generically, so a new value renders without code.
- **[verified]** The domain key used by existing callers is
  `$getDatabaseSettingsFromMainTable['domain']` (`analysis_list.php:157`, `overview.php:7`).

## Design

### Gates (every call placement: Sync, Call selected, Call again, Retry sending)
A call may be placed only if ALL of these hold. Otherwise nothing is reserved and nothing is sent.
1. `zenxai_crm_enabled` = 1, ZenxAI is configured, and the admin has `can_broadcast_messages`
   (all unchanged from SAN-1028).
2. `ai_credits_enabled` is truthy for the tenant. Otherwise the dashboard says "Voice calls need AI
   Credits. Contact support to enable AI Credits."
3. An `ai_voice_call` row exists in `ai_credit_task_rates` with `credits_per_unit > 0`. Otherwise:
   "Voice call pricing is not configured yet."
4. `getAiCreditAvailableBalance(domain) >= reserveCredits`, where `reserveCredits = rate ×
   reserveMinutes`. `reserveMinutes` = `$_ENV['ZENXAI_RESERVE_MINUTES']` (int, default **10**).
   When this fails, the batch stops with "Insufficient AI credits — N more needed" and a
   **Buy credits** link (`/ai_credits/buy`). Calls already placed in the batch are kept.

### Per-call credit lifecycle (`source_ref` = `"zenxai:" . zenxai_calls.id`)
| Moment | Credit action | `zenxai_calls` update |
|---|---|---|
| Row claimed (`pending_send`), gates pass | `reserveAiCredits(domain, reserveCredits, ref, 'ai_voice_call')` | `credit_status='reserved'`, `credits_reserved`, `credit_rate` |
| Reserve fails | No POST. The row is released (soft-deleted, as for 401/402/403 today). | — |
| Invalid phone | Never reserved | `credit_status` NULL |
| POST rejected with no call created (4xx other than 429, 401/402/403) | `refundAiCreditReservation` | `refunded` |
| 429 / 5xx / network (row kept for retry, SAN-1028 behaviour) | Reservation **kept** and reused on retry, never reserved twice | stays `reserved` |
| Retry-pending row later released | refund | `refunded` |
| Final `completed` | `settleAiCredits(domain, reserved, charge, ref, 'ai_voice_call', 1, [], 'VOICE_CALL')` | `settled`, `credits_charged`, `billed_minutes` |
| Final `no_answer` / `busy` / `failed` / `cancelled` | refund (full) | `refunded` |

- **Charge formula:** `billed_minutes = min(max(1, ceil(duration_sec / 60)), reserveMinutes)`;
  `charge = billed_minutes × credit_rate`. This bills per started minute, with a 1-minute minimum
  for a connected call and a cap at the reservation. Sanchi absorbs any overage beyond the cap, and
  the overage is logged. The rate snapshot (`credit_rate`) protects in-flight calls from operator
  rate edits.
- **Settle failure** (balance dropped below the charge between reserve and settle; unlikely,
  because the reservation was pre-checked against the available balance): retry once. If it still
  fails, leave `credit_status='reserved'` and log. The ZenxAI reconcile (below) retries it later.
  Never force the balance negative.
- **Idempotency:** the existing RESERVE→DEBIT/REFUND row-claim makes settle and refund safe
  against double Refresh and against the reconcile racing a Refresh. `credit_status` is updated
  only after a successful claim.

### Stale reservations (fixes the "6-hour auto-refund" risk)
- `reconcileStaleAiCreditReservations()` **excludes** `source_ref LIKE 'zenxai:%'`, NULL-safe:
  `(source_ref IS NULL OR source_ref NOT LIKE 'zenxai:%')`. Existing analysis reservations are
  reconciled exactly as today.
- New `zenxaiReconcileCreditReservations($database, $domain, $limit = 20)` in
  `includes/zenxai_functions.php`:
  - Loads this tenant's `zenxai_calls` with `credit_status='reserved'` that are older than 15
    minutes.
  - With a `call_id`: polls `GET /calls/{call_id}` (rate limiter applies). A final status settles or
    refunds; a non-final one is left as is.
  - Without a `call_id`, older than 1 h: refund.
  - A ZenxAI 404 refunds.
- Where it's called:
  - dashboard page load
  - "Refresh all non-final"
  - `modules/ai_credits/overview.php`, **only when `zenxai_crm_enabled` = 1 and ZenxAI is
    configured**, placed after the existing reconcile call. With the flag off, overview.php
    behaves exactly as today.

### Sanchi's ZenxAI balance runs out (402 `insufficient_balance`)
- The tenant sees "Voice calls are temporarily unavailable. Please try later or contact
  support". The tenant is never told it's a wallet problem, because that balance is Sanchi's.
- The reservation is refunded.
- Capture a Sentry event: `\Sentry\captureMessage('ZenxAI platform wallet empty (402)')`, guarded
  by `function_exists`, with the tenant domain as a tag. The admin Sentry SDK is initialised in
  `index.php`.

### Dashboard additions (SAN-1028 page)
- **Header:** available AI Credits, the rate ("N credits per minute ≈ reserve R per call"), and a
  **Buy credits** link.
- **Per call:** a "Credits" column (`reserved R` / `charged C (M min)` / `refunded` / `—`).
- **Sync confirmation modal:** "Up to N calls. Reserves up to N×R credits. Only connected minutes
  are charged; unanswered calls are refunded."
- **Draft Applications dev-only hint** (uncommitted change already in the working tree): add the
  credits gates, i.e. `ai_credits_enabled` off and `ai_voice_call` rate missing.

## Changes per repo

### tenants (SAN-1136)
Append `AI_VOICE_CALL = 'ai_voice_call'` to `AiTaskType` and `VOICE_CALL = 'VOICE_CALL'` to
`AiLedgerSourceType`. Append only: no rename, no reorder.

### tenants-admin (SAN-1137)
Append `'ai_voice_call'` to the fallback list at `modules/ai_credits/task_rates.php:37`. Nothing
else changes.

### backend (SAN-1138)
Add nullable columns to `zenxai_calls`: `credit_status` varchar(20), `credits_reserved` int,
`credits_charged` int, `billed_minutes` int, `credit_rate` int.

### admin (SAN-1139)
- **`includes/ai_credits_functions.php`**, backward-compatible only:
  - `reserveAiCredits($domain, $credits, $sourceRef, $taskType = null)`. The insert includes
    `task_type` only when it isn't null, so the existing insert is unchanged.
  - `settleAiCredits(..., $costData, $sourceType = 'ANALYSIS')`, replacing the hardcoded
    `'ANALYSIS'`.
  - The reconcile exclusion described above.
  - **No other line changes.**
- **`includes/zenxai_functions.php`:** gate helpers, reserve/settle/refund hooks at the lifecycle
  points above, and `zenxaiReconcileCreditReservations`.
- **`modules/application_management/zenxai_dashboard.php` + template:** gates, header, column,
  modal copy.
- **`modules/ai_credits/overview.php`:** one guarded call after line 43.
- **`history.php` / `overview.php` templates:** none needed. A voice RESERVE row carries
  `task_type` and so is not mislabelled.
- **Module specs:** `ai_credits`, `application_management`, and the backend zenxai spec.

## Non-regression checklist (must all pass; primary acceptance)
- [ ] Every existing caller of `reserveAiCredits` / `settleAiCredits` / `refundAiCreditReservation`
      / `debitAiCreditsInstant` is unchanged (grep proves the argument lists are the same), and its
      ledger rows are identical (`analysis_list.php`, `analysis_result.php`, `analysis_form.php`).
- [ ] An existing analysis run's RESERVE → settle, and its RESERVE → refund, give a byte-identical
      ledger/wallet diff before and after this change (scratch DB harness).
- [ ] `reconcileStaleAiCreditReservations` still refunds a stale analysis reservation (including
      one with a NULL `source_ref`) and skips a `zenxai:` one.
- [ ] Purchase (Easebuzz), grants, packages, task-rates CRUD, history, overview and invoices
      behave as before. With the flag off, `overview.php` renders byte-identical.
- [ ] SAN-1028 behaviour is unchanged apart from the added gates and columns: the duplicate guard,
      idempotency keys, rate limiter and CSRF.

## Acceptance (feature)
- [ ] The gates block with the exact messages above, and nothing is reserved or sent.
- [ ] A completed 61 s call charges 2 min × rate; a 5 s call charges 1 min; a 30 min call charges
      the reserve cap.
- [ ] no_answer / busy / failed / cancelled / rejected / invalid calls are never charged.
- [ ] A double Refresh, and a Refresh racing the reconcile, settle exactly once.
- [ ] A 402 shows the neutral message, refunds, and sends a Sentry event.
- [ ] Ledger rows: RESERVE with `task_type=ai_voice_call`; DEBIT with `source_type=VOICE_CALL`.

## Test plan
- Scratch-only harness (SQLite/MySQL via Medoo plus a local mock ZenxAI), as in SAN-1028. **No
  request to crm.zenxai.io.**
- `php -l` on all touched files, `npm run build` / `tsc` for tenants and backend, and `/check-isolation`.
- No automated test framework exists (the guardian skill is missing); verification is by harness
  and lint.

## Rollout
1. Deploy tenants, then tenants-admin, then backend, then admin (as for SAN-1028).
2. The operator creates the `ai_voice_call` rate in Task Rates, e.g. 8 credits/min ≈ ₹8/min at
   ₹1/credit. Voice-named packages are optional.
3. Only then enable `zenxai_crm_enabled` for a tenant. Without the rate row, calls are blocked with
   "pricing not configured".

## Implementation notes (2026-09-29, spec-implementer)

All four repos implemented on `ai_native_setup`, **uncommitted** (user reviews diffs first). Linear:
SAN-1136/1137/1138/1139 moved Todo → In Progress → In Review.

**Dependency caveat:** `depends_on` lists SAN-1028 (`in-review`) and FT-005 (`draft`), and neither is `done`. The
work went ahead because FT-005 documents AI Credits code that is already live, and SAN-1028's code is committed
on `ai_native_setup`. Nothing was committed, so the user can hold this change until SAN-1028 is closed.

**Gates run (manually; the slash-command skills aren't callable from the implementer):**
- **API contract:** the backend diff touches only the entity and the module spec, with no controller, DTO or
  route change. In tenants, the public `GET /ai-credits/task-rates` shape is unchanged.
- **Isolation, admin:**
  - The wallet and ledger are reached only through `ai_credits_functions.php` helpers, plus one domain-scoped
    RESERVE-row read, all keyed by `$getDatabaseSettingsFromMainTable['domain']`, never by request input.
  - `zenxai_calls` stays on the per-tenant `$database`, and only stored `call_id`s are polled.
  - The advisory-lock name is `md5(domain)`-scoped.
  - The harness confirms that the other tenant's wallet and ledger are never touched.
- **Flags:** no flag trace was needed, since no new flag was added.

**Non-regression evidence** (scratch MySQL 9.6 + Medoo from this repo; HEAD copy vs working tree):
- **Caller list:** all 14 existing call sites of the five helpers are byte-identical, including line numbers.
- **Ledger and wallet diff:** analysis reserve→settle, a double settle, reserve→refund, a double refund, an
  insufficient-balance settle and two instant debits give byte-identical ledger, wallet and SQL (23 statements).
- **6-hour reconcile:** the only difference is that the stale `zenxai:` row is skipped. The NULL-`source_ref`
  row is still selected and ends in the same state as before. The generated SQL is
  `... AND (source_ref IS NULL OR (source_ref NOT LIKE 'zenxai:%'))`.
- **overview.php:** with the flag off, or the flag on but ZenxAI unconfigured, the rendered page is identical to
  HEAD after timestamp normalisation, and no ZenxAI request is made.

**Feature harness:** 81/81 checks passed against a local mock of the 3 ZenxAI endpoints (no request left
127.0.0.1). It covers:
- the gates
- the charge boundaries: 0, 5, 60, 61, 600, 601 and 1800 s, plus a null duration
- the rate snapshot
- refunds for every unanswered status, rejection and 404
- a 429/5xx retry reusing one reservation
- a 402 with its Sentry tag
- 3 concurrent Refreshes racing 3 concurrent reconciles, which settle exactly once
- the SAN-1028 duplicate guard, idempotency keys, CSRF, rate limiter and isolation

Choices made where the spec was silent (none change a contract):
- **Resumed claims:** when the reservation fails for a *resumed* `pending_send` claim (legacy, or already
  refunded by the reconcile), the claim is kept for a later retry rather than soft-deleted. The call may
  already exist at ZenxAI, so it must stay trackable. New claims are soft-deleted as the spec says.
- **Double balance check:** the balance is checked once before the claim row is created, and again under a
  per-tenant `GET_LOCK` at reserve time. This stops two concurrent batches from passing against the same
  balance.
- **Deploy-order guard:** if the SAN-1138 columns aren't deployed yet, placement is blocked with the neutral
  "temporarily unavailable" message, so a reservation is never made that the row can't track.
- **Reconcile scope:** the reconcile also immediately refunds released (soft-deleted) rows and call-less rows
  that aren't `pending_send`. Rows that are already final locally are settled or refunded without a poll.
- **404 refunds** happen inside `zenxaiRefreshCall()`, so a manual Refresh that gets a 404 refunds too, not
  only the reconcile.
- **"Refresh all non-final"** runs the reconcile on its first batch only, with a limit of 5.
- **402 message:** the text changed everywhere `zenxaiFatalMessage()` is used (place, refresh, cancel). Sentry
  is captured on call placement only.
- **Credit gates** don't hide the Draft Applications button, because the dashboard explains them. For devs
  they are appended to the hidden-button notice, or shown as an info icon next to a visible button.
- **Rate field:** only `credits_per_unit` is used; `rate_mode = cost_multiplier` is ignored for `ai_voice_call`.
- **`zenxaiStartCall()`** gained a required `$billing` parameter. It has 2 callers, both in
  `zenxai_dashboard.php`.

Pre-existing, not changed: a stale RESERVE row with a NULL `source_ref` can never be refunded. It is selected,
but `refundAiCreditReservation()` matches `source_ref = ?`, so it never claims the row.

Follow-up: add `ZENXAI_RESERVE_MINUTES` to the env-key list in `sc-saas-admin/CLAUDE.md`. It is already
documented in the `application_management` module spec.

## SAN-1150 ledger trail (2026-09-29, sc-saas-admin only, uncommitted)

**Problem.** Balances were correct, but the ledger misled a client's finance team:
1. The overview/history templates showed RESERVE rows as "DEBIT" with a "−" (`$typeLabel = reserve → 'debit'`).
2. REFUND rows showed "+N", although releasing a hold never changes the balance.
3. `settleAiCredits` / `refundAiCreditReservation` convert the RESERVE row in place, so the hold vanished
   and there was no "charged X, released Y" breakdown.

**Decision (user): fix for new rows only.** Existing ledger rows are not rewritten or migrated.

**A. Append-only voice trail.** New `zenxaiVoiceLedgerResolve()` (+ `zenxaiVoiceLedgerSettle` /
`zenxaiVoiceLedgerRelease`) in `includes/zenxai_functions.php`; `zenxaiSettleCallCredits` and
`zenxaiRefundCallCredits` (the only voice settle/refund paths: completed, unanswered, rejected POST, 402,
401/403 release, cancel, 404, reconcile) now call them instead of `settleAiCredits` /
`refundAiCreditReservation`. One `$mainDatabase` transaction:
- Claim the single open hold (`credit_type='RESERVE' AND source_type='RESERVE'`, `FOR UPDATE`) by setting
  `source_type='VOICE_CALL'`; rowCount must be 1. The HOLD row keeps credit_type RESERVE, task_type,
  amount, balance_after and created_at.
- Answered: wallet `balance -= charge, reserved_balance -= held, total_consumed += charge WHERE balance >= charge`
  (0 rows → rollback), then DEBIT (charge) and, if held > charge, REFUND "release" (held − charge).
- Not answered / failed / rejected: `reserved_balance -= held`, one REFUND "release" (held).
- New rows: `source_type VOICE_CALL`, same `source_ref`, `task_type ai_voice_call`, `applicant_count 1`,
  `balance_after` = wallet balance after the change, `created_at` = PHP `date()`.
- `zenxaiOpenReservation()` now requires `source_type='RESERVE'`.

`includes/ai_credits_functions.php` is **unchanged** (`git diff` empty; SHA-1 5546e93d… equals HEAD), so the
AI Analysis flow is byte-identical. Example (68 s call, rate 8, 80 held): HOLD 80 → DEBIT 16 → RELEASED 64;
balance −16, reserved back to 0, consumed +16.

**B. Display (all rows, presentation only).** `includes/ai_credits_ledger_display.php` (`aicLedgerRowView`)
is used by the ai_credits overview/history templates and the dashboard modal:
- RESERVE → amber HOLD "N held", tooltip "Reserved from available credits; balance unchanged", and a
  "settled" note when `source_type=VOICE_CALL`.
- REFUND → blue-grey RELEASED "N released", "balance unchanged".
- DEBIT → "−N"; CREDIT → "+N".
- Friendly source labels, "call #N" for voice rows, and the legend line.
- New CSS classes `aic-badge-hold` / `aic-badge-released` (+ helpers) in `ai-credits-shared.css`.
- Ledger lists sort `created_at DESC, id DESC`.

**C. View ledger.**
- `history.php` has a whitelisted `task_type` filter, with a chip and a clear link, kept in the form and
  in pagination links.
- The dashboard AI Credits card has a **View ledger** link (`/ai_credits/history?task_type=ai_voice_call`).
- The call-details modal has a **Credit ledger** section. It uses one domain-scoped query for the calls on
  the page (`source_ref IN ('zenxai:<ids>')`).
- Credits-column wording is `held R` / `charged C (M min)` / `not charged`. The stored `credit_status`
  values are unchanged.

**Cross-repo grep (all 7 repos).** Only sc-saas-admin reads ledger RESERVE rows. That covers
`ai_credits_functions.php`, `analysis_list.php` and `analysis_result.php` (all by folder-id `source_ref`,
never `zenxai:`), plus `zenxai_functions.php`. `sanchiconnect-saas-tenants` only writes PURCHASE CREDIT
rows and declares the enums; `VOICE_CALL` already exists in `AiLedgerSourceType`. `sanchiconnect-saas-tenants-admin`
only writes GRANT CREDIT rows. backend, frontend, the analyzer and webservices have no ledger access.
Nothing depends on RESERVE rows disappearing. `reconcileStaleAiCreditReservations()` excludes `zenxai:%`,
so persistent voice holds are never refunded by it.

**Evidence** (scratch MySQL 9 + local mock, harness in the session scratchpad; no request to crm.zenxai.io):
- **AI Analysis unchanged:** `credits_scenario.php` flows + reconcile, run with the HEAD file and the
  working-tree file, give byte-identical output.
- **Voice trail:** `ledger_trail_tests.php` passes 27/27. It covers answered 68 s / 9 s / cap, the four
  unanswered statuses, 400, 402 (Sentry still sent), cancel, double Refresh, and a 9-process race (Refresh +
  batch reconcile + overview reconcile) giving exactly one DEBIT + one RELEASED. It also covers settle with
  an insufficient balance (whole transaction rolled back, hold still open), 429 then resume, an old-scheme
  open hold created by the HEAD code and resolved by the new code, and an old converted row never touched
  again. Both reconciles skip resolved holds, and the other tenant is untouched.
- **SAN-1136 regression:** `feature_tests.php` passes 81/81, with the ledger-shape assertions updated to the trail.
- **Rendering:** `render_tests.php` passes 30/30. It checks labels and signs for new trail rows, old
  converted rows, analysis, purchase and an open hold. It also checks XSS escaping, the task_type filter
  (combined, pagination, unknown value ignored), the credit_type filter, the overview, the dashboard View
  ledger link and the modal Credit ledger, with no PHP warnings.
- **Lint:** `php -l` passes on all touched files, and `node --check` passes on the inline JS of the 3
  rendered pages.

**Known, not changed:**
- A crash between the ledger commit and the `zenxai_calls.credit_status` update leaves the row `reserved`
  while its hold is resolved. There is no double charge, but the column shows `held R`. This is a pre-existing
  window.
- `settleAiCredits` / `refundAiCreditReservation` restamp `created_at` with MySQL `NOW()`, while the
  templates assume UTC. Analysis rows can show a time-zone-shifted time.

## Out of scope
- Separate voice-only wallets or package-specific rates.
- Automatic billing against Sanchi's ZenxAI plan tier.
- A cron-based reconcile; the on-demand reconcile runs on page load.
- Charging for unanswered calls. Assumed free until ZenxAI confirms otherwise; changing this
  later is a one-line rule change.

## Open questions
None blocking. External follow-ups for ZenxAI:
- Do unanswered or busy calls cost Sanchi anything?
- Is billing per second or per started minute?
The rules above are the safe default either way.
