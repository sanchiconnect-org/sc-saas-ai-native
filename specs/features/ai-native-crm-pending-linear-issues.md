# AI-Native CRM — Linear issues still to be created

**Status:** CANCELED 2026-10-19 — the AI-Native CRM project was shut down and all its Linear issues canceled; never implemented. Do not create the issues below.
**Created:** 2026-08-07
**Project:** [AI-Native CRM — Client Pipeline, Revenue Intelligence & Invoice Automation](https://linear.app/sanchiconnect/project/ai-native-crm-client-pipeline-revenue-intelligence-and-invoice-f33e4c9fa226)
**Source:** `SanchiConnect_AI_CRM_BRD_v2.pdf` (BRD v1.0, Prabs, Aug 07 2026)

17 of the 27 planned issues were created (SAN-259 … SAN-275). The Linear workspace then hit its **free-tier issue limit** — `"You've exceeded the free issue limit for this workspace"`. The 10 issues below are written out in full, ready to paste into Linear once the plan is upgraded.

**Build-order positions** (full 27-task order is in the Linear project description):

| Order # | Issue below | Wave |
|---|---|---|
| 14 | §2 Invoice review UI + GST PDF | 3 — Invoice Engine |
| 15 | §9 Invoice email dispatch | 3 — Invoice Engine |
| 17 | §10 Slack alert delivery | 4 — Automation |
| 18 | §1 Renewals Radar | 5 — Views |
| 22 | §3 Churn risk score | 6 — AI Layer |
| 23 | §4 Upsell signal | 6 — AI Layer |
| 24 | §5 Relationship summary | 6 — AI Layer |
| 25 | §6 Revenue anomaly alert | 6 — AI Layer |
| 26 | §7 Linear issue drafter | 6 — AI Layer |
| 27 | §8 Invoice dispute classifier | 6 — AI Layer |

Every one carries: `Repo:` label, `Feature` label, priority, state **Backlog**, and no cross-repo dependency.

**Assignees (per user instruction, 2026-08-07 — overrides the documented mapping):**

| Repo label | Assignee | Note |
|---|---|---|
| `Repo: Tenants-Admin` | **Sandeep** | user instruction: "admin task to sandeep" |
| `Repo: Tenants` | **Aman kabra** | user instruction: "backend task to Aman" |
| `Repo: AI Analyzer` | Nirmal Singh | not covered by the instruction — documented mapping stands |
| `Repo: 3rdparty Webservices` | Nirmal Singh | not covered by the instruction — documented mapping stands |

This departs from the fixed repo→developer mapping in `specs/spec-authoring-practices.md`, which routes `sanchiconnect-saas-tenants` and `sanchiconnect-saas-tenants-admin` to Nirmal Singh and reserves Sandeep for `sc-saas-admin` and Aman for `sc-saas-backend`. The override is deliberate — it assigns by skill (PHP admin panel → Sandeep, NestJS API → Aman) rather than by repo name. The same override was applied to the 17 issues already created (SAN-259 … SAN-269 → Aman, SAN-270 … SAN-275 → Sandeep).

---

## 1. `Repo: Tenants-Admin` · Priority: High (2)

### Every contract expiring in the next 90 or 180 days is visible on one screen, biggest first

**Module:** M5 — Renewals Radar · **Phase:** 5 · **Repo:** `sanchiconnect-saas-tenants-admin`

**Problem + Who** — Renewals are missed because nothing surfaces an approaching contract end until it has passed. Account Managers cannot prioritise which renewals to work first, so a ₹8,00,000 account gets the same attention as a ₹1,10,000 one — or less (BRD P3, P4).

**Outcome** — An Account Manager opens one screen and sees every contract ending within the next 90 or 180 days, ordered by contract value, with its renewal likelihood alongside.

**Acceptance Criteria**
1. The radar lists every client whose Contract End Date falls within the next 90 days.
2. A 180-day window can be selected and shows the wider set.
3. Rows are sorted by ACV descending — the largest contract at risk appears first.
4. Each row shows client name, ACV, contract end date, days remaining, account manager, and renewal probability.
5. Clients already renewed (a newer active contract version exists) do not appear as at-risk.
6. Churned clients do not appear.
7. A PO spot-check of the listed contract end dates against the records finds no incorrect or missing entry.
8. An Account Manager sees their own accounts; a wider role sees all.

**Scope — In** — The renewals radar view, its 90/180-day windows, sorting, already-renewed and churned exclusion, role-aware visibility.

**Scope — Out** — The weekly renewal-nudge automation and its Slack alert (separate issues, other repos). Renewal probability scoring itself (AI-layer issue) — this view only displays it. Contract versioning semantics.

**Context** — BRD §5.5 Renewals Radar row. The already-renewed exclusion is the part that quietly breaks: BRD automation A3 names "no false positives for already-renewed contracts" as its acceptance criterion and the same trap applies here. A client with an expiring base contract *and* an active renewal is not at risk; showing it as such trains people to ignore the screen. Reads the tenants MySQL DB directly.

**Satisfies** — AC-11.

---

## 2. `Repo: Tenants-Admin` · Priority: High (2)

### Finance can review, approve and dispatch a GST-compliant invoice PDF without building it by hand

**Module:** M4 — Invoice & Payment Management (operator UI + PDF) · **Phase:** 3 · **Repo:** `sanchiconnect-saas-tenants-admin`

**Problem + Who** — Finance creates every invoice manually, which delays dispatch and therefore cash collection (BRD P2). Even once invoice records exist, there is no screen to review a draft, approve it, attach a compliant PDF and mark it sent or paid — so the record cannot replace the manual process.

**Outcome** — Finance opens a draft invoice, checks it, approves it, and dispatches a correctly formatted GST invoice PDF — and later records the payment against it.

**Acceptance Criteria**
1. A queue lists invoices by status: Draft, Sent, Paid, Overdue, Disputed.
2. Opening a Draft shows client, GSTIN, invoice number, period covered, amount excl. GST, GST rate and amount, total, TDS if applicable, and net payable.
3. Approving a Draft moves it to Sent and attaches the generated PDF.
4. The generated PDF contains client name, GSTIN, invoice number, HSN/SAC code, GST rate, GST amount, total, and the period covered — and Finance signs off on the template.
5. Marking an invoice Paid requires a payment date and accepts a payment reference.
6. An invoice can be flagged Disputed with notes.
7. Invoice screens are visible to Finance and not to Account Managers.
8. An invoice cannot be edited after it is Paid.

**Scope — In** — Invoice queue and detail screens, approve/dispatch/mark-paid/dispute actions, the GST invoice PDF template and its generation, role gating.

**Scope — Out** — Emailing the PDF to the client (3rdparty-webservices issue). Auto-creating drafts on a schedule (SAN-268). The invoice schema and lifecycle rules (SAN-266, SAN-267). Client self-service download — OQ-04, out of scope.

**Context** — BRD §5.4 and AC-08. **Two BRD §11 open questions gate the template and must be answered by Finance before sign-off:** OQ-02 (GST treatment for educational institution clients — exempt or 18%?) and OQ-07 (are TDS certificates tracked in the CRM or outside?). Build the template so an exempt rate renders correctly; do not assume 18% is the only case. Note also that **HSN/SAC code is required on the PDF by AC-08 but appears nowhere in the BRD §6 data model** — confirm with Finance whether it is per-contract or a single company-wide service code before hardcoding one.

**Satisfies** — AC-08.

---

## 3. `Repo: AI Analyzer` · Priority: High (2)

### An Account Manager sees which accounts are at risk of churning, and why, before the client tells them

**Module:** M7 — AI Intelligence Layer · **Phase:** 6 · **Repo:** `ai-startups-analyzer`

**Problem + Who** — Account management is reactive. Churn is discovered after it has happened, when a client declines to renew (BRD P5). No signal exists that would let an AM intervene while the relationship is still recoverable.

**Outcome** — Every client carries a Red / Amber / Green churn-risk badge that refreshes at least weekly and shows the signals that produced it.

**Acceptance Criteria**
1. Every client is scored Red, Amber or Green.
2. The score refreshes at least once a week without anyone triggering it.
3. Opening the score reveals the signals that drove it — days since last interaction, payment delays, contract age, NPS where available — each with its contribution.
4. A client with a long gap since last interaction and a history of late payments scores worse than one with neither.
5. A client with no interaction history yet is not scored Red purely for absence of data; insufficient-data is distinguishable from at-risk.
6. Re-scoring the same unchanged client twice gives the same result — the score is not visibly noisy run to run.
7. The score is exposed for other systems to read; the AM-facing badge reads from it.
8. The PO reviewing an explanation card can name the signals used.

**Scope — In** — The churn-risk scoring service, its weekly schedule, the signal-contribution explanation, and the read API.

**Scope — Out** — The badge UI on the client card (tenants-admin). Upsell, relationship summary, anomaly detection, issue drafting, dispute classification (separate issues). Acting on the score.

**Context** — BRD §5.7 (Churn Risk Score row) and §8 AI Transparency NFR: "AI-generated scores must show the signals that drove the output." **OQ-06 is unresolved and owned by the CTO** — OpenAI / Anthropic / local model, and the data-residency implications. This repo already supports multiple providers behind `DEFAULT_PROVIDER`, so build against that abstraction and let the CTO's ruling pick the provider; do not hardcode one. This scores SanchiConnect's own client accounts — a distinct concern from the existing startup-application scoring in this repo, and it must not be conflated with it.

**Satisfies** — AC-12.

---

## 4. `Repo: AI Analyzer` · Priority: Medium (3)

### Sales is told which accounts are underpriced against their cohort, and by how much

**Module:** M7 — AI Intelligence Layer · **Phase:** 6 · **Repo:** `ai-startups-analyzer`

**Problem + Who** — Upsell opportunities are found by chance. Nobody systematically compares an account's contract value against comparable accounts, so clients paying well below their cohort go unnoticed until renewal — if then (BRD P5).

**Outcome** — Accounts priced below their cohort surface as flagged upsell opportunities with a suggested amount and a suggested time to raise it.

**Acceptance Criteria**
1. Each client's ACV is compared against the median ACV of its cohort (organisation type, and programme size where available).
2. Clients materially below their cohort median are flagged.
3. Each flag carries a suggested upsell amount and a suggested timing.
4. The suggested timing relates to the account's renewal window rather than being arbitrary.
5. The signals behind each flag are visible — cohort used, cohort median, this client's ACV, growth indicators.
6. A client that is at or above its cohort median is not flagged.
7. A cohort with too few members to have a meaningful median produces no flag rather than a spurious one.
8. Flags refresh on a schedule and do not need manual triggering.

**Scope — In** — Cohort construction, median comparison, upsell flag with amount and timing, signal explanation, read API.

**Scope — Out** — The cohort *view* in the admin UI (SAN-275 — different thing, same word). Acting on or tracking upsell outcomes. Other AI features. Usage-data ingestion where no usage data exists yet.

**Context** — BRD §5.7 Upsell Signal row: input signals are current ACV vs. cohort median, programme growth indicators, and usage data if available; output is a flag plus suggested upsell amount and timing. With 28 clients, several cohorts will be too small for a stable median — criterion 7 is the one that keeps this honest rather than noisy. OQ-06 (AI provider, data residency) applies here too.

---

## 5. `Repo: AI Analyzer` · Priority: Medium (3)

### An Account Manager can catch up on any account in three sentences before a call

**Module:** M7 — AI Intelligence Layer · **Phase:** 6 · **Repo:** `ai-startups-analyzer`

**Problem + Who** — Before a client call, an AM has to read back through scattered notes, emails and interaction logs. Leadership walking into a meeting has no quick way to know where a relationship stands. The context exists but is not readable at a glance.

**Outcome** — Every client carries an auto-generated three-sentence account brief, refreshed weekly, drawn from its logged interactions and notes.

**Acceptance Criteria**
1. Each client has a summary of roughly three sentences.
2. The summary refreshes at least weekly without manual triggering.
3. It covers relationship state, recent activity, and anything outstanding.
4. It is drawn only from that client's logged interactions, notes and emails where connected — no invented facts, and no detail from another client.
5. The sources it drew from are identifiable.
6. A client with no logged interactions produces an explicit "no interaction history" rather than a fabricated summary.
7. A stale summary is visibly dated, so nobody mistakes a three-week-old brief for current.

**Scope — In** — The summarisation service, its weekly schedule, source attribution, and the empty-history case.

**Scope — Out** — Email integration itself (where emails are not connected, this works from logged interactions only). The UI panel that displays the brief. Other AI features.

**Context** — BRD §5.7 Relationship Summary row — inputs are all logged interactions, emails if connected, and notes; output is an auto-generated 3-sentence brief updated weekly, consumed by Account Managers and Leadership. Criterion 4 is the load-bearing one: a summary that invents plausible relationship history is worse than no summary, because it will be trusted and repeated in a client meeting. OQ-06 applies.

---

## 6. `Repo: AI Analyzer` · Priority: Medium (3)

### Finance is alerted when a client's projected revenue drops more than 20% against the same period last year

**Module:** M7 — AI Intelligence Layer · **Phase:** 6 · **Repo:** `ai-startups-analyzer`

**Problem + Who** — A client quietly reducing scope, delaying payments or shrinking its contract shows up in the numbers long before anyone reads those numbers. Finance and Leadership currently find out at the aggregate level, at quarter end, when the shortfall is already booked.

**Outcome** — When a client's projected revenue falls materially against its own history, Finance and Leadership are alerted while there is still time to respond.

**Acceptance Criteria**
1. Each client's FY Revenue is compared against its prior FY, and its rolling windows against the equivalent historical windows.
2. A drop of more than 20% against the same period raises an alert.
3. The alert names the client, the size of the drop, and the comparison period used.
4. A client whose contract legitimately ended does not raise an anomaly alert — an expected ₹0 is not an anomaly.
5. A client with no prior-year history is skipped rather than alerting on a 100% "drop".
6. The same anomaly does not re-alert every run once acknowledged.
7. Detection runs on a schedule and needs no manual trigger.

**Scope — In** — Historical comparison, the >20% threshold, alert generation with reasoning, expected-decline suppression, and re-alert suppression.

**Scope — Out** — Delivering the alert to Slack or email (3rdparty-webservices issue). The revenue calculations themselves (SAN-263, SAN-264). Other AI features.

**Context** — BRD §5.7 Revenue Anomaly Alert row: inputs are FY Revenue vs. prior FY and rolling windows vs. historical; alert if projected revenue drops >20% vs. same period; consumers are Finance and Leadership. Criteria 4 and 5 are what separate a useful alert from noise — with prepaid contracts, a legitimately expired contract shows a 100% drop, and alerting on it every run is exactly how a team learns to ignore alerts. OQ-06 applies.

---

## 7. `Repo: AI Analyzer` · Priority: Medium (3)

### The Product Owner can turn a spoken or typed need into a properly formed Linear issue in under two minutes

**Module:** M7 — AI Intelligence Layer · **Phase:** 6 · **Repo:** `ai-startups-analyzer`

**Problem + Who** — Features are requested informally and shipped inconsistently because there is no formal spec gate (BRD P6). Writing a well-formed issue — problem, outcome, observable acceptance criteria, scope in and out — takes long enough that it often gets skipped, and a skipped issue becomes scope creep and rework downstream.

**Outcome** — The PO describes a need in their own words and gets back a complete, correctly structured Linear issue draft in under two minutes.

**Acceptance Criteria**
1. A described need — typed or spoken — produces a draft issue.
2. The draft carries exactly the required fields and no more: Title, Problem + Who, Outcome, Acceptance Criteria, Scope — In, Scope — Out, Context, Priority.
3. The Title is outcome-shaped — what a user can now do — not a task or a solution.
4. Acceptance criteria are observable business checks, not implementation detail: "FY Revenue shows ₹0 when all payments fall before Apr 1" passes; "use fyStartAdj" does not.
5. Scope — Out is populated, not left blank.
6. Where the description peels back to a different underlying need than the solution framing given ("add a button"), the draft names the underlying need.
7. The PO times their own workflow at under two minutes from description to a draft they would mark Ready.
8. The draft is presented for review and edit before anything is created — it is never filed automatically.

**Scope — In** — The issue-drafting service, the required-field structure, the outcome-shaped title and observable-criteria rules, and voice or text input.

**Scope — Out** — Filing directly into Linear without review. Drafting the technical spec — that is `/from-linear` and the `spec-author` agent, a separate step in the loop. Other AI features.

**Context** — BRD §5.7 Linear Issue Drafter row, §7.1 build loop steps 1–6, and §7.2 The Issue Anatomy (the exact required field list and worked examples). AC-13 measures it: PO generates a correctly-structured issue from a described need in under 2 minutes, timing their own workflow. Criterion 8 matters — this drafts *for* the PO, who owns the What and Why; auto-filing would hand a product decision to the tool. OQ-06 applies.

**Satisfies** — AC-13.

---

## 8. `Repo: AI Analyzer` · Priority: Low (4)

### A disputed invoice arrives at Finance already categorised and prioritised

**Module:** M7 — AI Intelligence Layer · **Phase:** 6 · **Repo:** `ai-startups-analyzer`

**Problem + Who** — When a client disputes an invoice, Finance triages it by reading the dispute notes and the client's history from scratch. Similar disputes get inconsistent handling, and the ones that need urgent attention are not distinguished from routine queries.

**Outcome** — Every disputed invoice carries a suggested resolution category and a priority, derived from the dispute notes and that client's invoice history.

**Acceptance Criteria**
1. Flagging an invoice Disputed produces a suggested resolution category.
2. Categories cover at least: amount incorrect, GST or TDS query, service not delivered, payment already made, and other.
3. Each suggestion carries a priority.
4. The reasoning is visible — which dispute-note phrases and which history drove the categorisation.
5. A client with a history of disputes that resolved in their favour is prioritised differently from a first-time disputer.
6. Finance can override the suggested category, and the override is recorded.
7. A dispute with notes too thin to categorise returns "needs review" rather than guessing a category.

**Scope — In** — The dispute classification service, category taxonomy, priority assignment, reasoning exposure, and the override path.

**Scope — Out** — Resolving disputes. The dispute-flagging UI (tenants-admin invoice issue). Other AI features. Automated client communication about a dispute.

**Context** — BRD §5.7 Invoice Dispute Classifier row: inputs are dispute notes, invoice history and the client record; output is a suggested resolution category plus priority; consumer is Finance. Lowest-priority AI feature — it only has value once invoices are live and disputes are actually being logged, so it should follow the invoice engine rather than lead it. OQ-06 applies.

---

## 9. `Repo: 3rdparty Webservices` · Priority: Medium (3)

### An approved invoice reaches the client's inbox with its PDF attached, and the send is recorded

**Module:** M6 — Automation Layer (email delivery leg) · **Phase:** 3–4 · **Repo:** `sc-saas-3rdparty-webservices`

**Problem + Who** — Approving an invoice in the CRM does not put it in front of the client. Without a delivery path, Finance still sends every invoice by hand, and the automation gains nothing (BRD P2). There is also no record of whether a given invoice was actually sent, so chasing an overdue payment starts with "did we even send it?".

**Outcome** — An approved invoice is emailed to the client's primary contact with its PDF attached, and the outcome of that send is recorded.

**Acceptance Criteria**
1. An invoice email can be sent to a named recipient with the invoice PDF attached.
2. The email carries the invoice number and due date in its subject.
3. A successful send returns confirmation the caller can store against the invoice.
4. A failed send returns a clear, actionable error — bad address, provider rejection, attachment too large — and does not silently succeed.
5. A transient provider failure is retried, and a retry does not send the client two copies.
6. Sending to an invalid address is reported back rather than swallowed.
7. The endpoint requires authentication.
8. Delivery attempts are logged with enough detail to answer "was this invoice sent, when, and to whom?".

**Scope — In** — The invoice email endpoint, PDF attachment handling, delivery-result reporting, retry with duplicate-send protection, auth, and delivery logging.

**Scope — Out** — Generating the PDF (tenants-admin issue). Deciding when to send (the CRM and Make.com own that). Invoice state changes. Slack alerts (separate issue). Client portal delivery — OQ-04, out of scope.

**Context** — BRD §5.4 (invoice dispatch) and §5.6 A1. **OQ-03 is unresolved and blocks the provider choice: "Which email system sends invoices? (Gmail, Zoho, Postmark, or other?)" — owner Finance + Engineering.** Do not pick one; build behind this repo's existing provider abstraction (it already fronts SendGrid and SES) so the ruling slots in. This repo is a stateless leaf node — it proxies to external providers and never calls back into any SanchiSaaS repo, so delivery results are returned to the caller, not written anywhere here.

---

## 10. `Repo: 3rdparty Webservices` · Priority: Medium (3)

### Overdue invoices and approaching renewals reach the right person in Slack, not a shared inbox nobody reads

**Module:** M6 — Automation Layer (Slack delivery leg) · **Phase:** 4 & 7 · **Repo:** `sc-saas-3rdparty-webservices`

**Problem + Who** — Four of the five BRD automations end in "notify via Slack" — new invoice drafts to Finance, overdue invoices to the Account Manager, renewal nudges, contract expiry alerts. None of them can complete, because there is no Slack delivery path. Every alert the CRM computes currently has nowhere to go.

**Outcome** — The CRM can deliver an alert to a specific person or channel in Slack, and knows whether it arrived.

**Acceptance Criteria**
1. An alert can be sent to a named Slack channel.
2. An alert can be sent directly to a named user — an AM receives overdue alerts for their own accounts, not a shared channel.
3. The message carries the context needed to act: client name, invoice number or contract, amount, date, and a link back to the record.
4. A successful send returns confirmation the caller can record.
5. A failed send returns a clear error and does not silently succeed.
6. An unknown user or channel is reported back rather than dropped.
7. The endpoint requires authentication.
8. An Account Manager confirms receipt of a Slack alert for every overdue invoice on their accounts.

**Scope — In** — The Slack delivery endpoint, channel and direct-message targeting, message formatting with a link back to the record, delivery-result reporting, and auth.

**Scope — Out** — Deciding when to alert or who to alert (the CRM and Make.com own that). Invoice or contract state changes. Email delivery (separate issue). Slack app installation and workspace configuration — an ops task, not code.

**Context** — BRD §5.6 A1, A2, A3 and A5, each of which ends in a Slack notification; AC-10 measures it — "Account Manager receives a Slack alert for every Overdue invoice on their accounts", confirmed by the AM. Criterion 2 is what AC-10 actually turns on: an alert broadcast to a shared channel does not satisfy "on their accounts". This repo is a stateless leaf node — it proxies outward and never calls back into any SanchiSaaS repo.

**Satisfies** — AC-10.
