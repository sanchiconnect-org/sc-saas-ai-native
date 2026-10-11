# SAN-1721 — Startup Details "Self Declaration" PDF: QA / UAT test script

**Owner (QA/UAT):** Ritu Raj. **Developer:** Aman Kabra. **Repo under test:** `sc-saas-admin` only (no backend, frontend or tenants change).
**Feature spec:** `specs/features/SAN-1721-startup-self-declaration-pdf.spec.md`. **Linear:** milestone "Startup Details — Self Declaration PDF" (SAN-1720 settings, SAN-1721 download button).

`sc-saas-admin` has no automated test suite, so this feature is verified by hand with this script. Every case lists **where to go**, **what to do**, and **what you should see**. Record Pass / Fail and a screenshot for every Fail. Reference layout: the `self.pdf` the product owner supplied (open it side by side for section 4).

## 0. What the feature is (read once)

On the admin **Startup Detail** page there is a new button **Download Self Declaration**. It downloads a one-page A4 PDF addressed to the Director, Directorate of Information Technology, Govt. of Tripura, titled "Self declaration", with five ticked certification lines, Notes, and a box holding Representative Name, Company Name and Date. The wording is an editable template in **Developer zone → Settings Management → Startup Grant Release Letter**. The button only shows when the tenant flag `startup_grant_release_format_download_enable` is **on** (the same flag as the Grant Release Letter).

## 1. Environment, accounts and test data

| Item | Value / how to get it |
|---|---|
| Admin URL | The tenant's admin site (local dev: `http://admin.localhost/`). Log in with an admin account. |
| Tenant flag | `tenant_users.startup_grant_release_format_download_enable` = 1 (ask the developer to switch it on/off; it is a tenants-DB column, not editable in the admin UI). |
| Account **A** | Super admin or Developer role. Can open Settings Management and every startup. |
| Account **B** | An admin role that can open Startup Detail but is **not** Super admin / Developer (cannot open Settings Management). |
| Account **P** | A **partner** login (`partner_id` session). Needs a startup created by this partner (**P-own**) and a startup created by a different partner or by admin (**P-other**). |
| Startup **S1** | A normal startup with an owner user (name e.g. "mohan") and company name e.g. "Coder Group". Local example: `/startup-detail/914/details`. |
| Startup **S-long** | Same as S1 but company name edited to 70+ characters, e.g. "Techcia International Services Private Limited Trading As Techcia Global Solutions India". |
| Startup **S-special** | Company name `A&B <Tech> "Labs" O'Neil Pvt Ltd` and owner name `Zoë Müller-Ñandi`. |
| Startup **S-blank** | A startup whose company name is empty (or whose owner user has an empty name). Ask the developer to blank it in the DB if the UI will not allow it. |
| Logo | A logo image uploaded in Settings Management (case 3.3). |

Tools: a PDF viewer, the browser's download list, and (for 6.x) the developer's `php_error.log`.

## 2. Gating: when the button and route are available

| # | Where to go / do | Expected |
|---|---|---|
| 2.1 | Flag **off**. Log in as A. Open **Startup / MSME list → open S1** (or `/startup-detail/{S1 id}/details`). Look at the buttons at the top right (Backdoor Login, Print, Message, Delete). | **No** "Download Self Declaration" button. The row above the buttons is empty. Everything else looks as before. |
| 2.2 | Flag **off**. Paste `/startup-detail/{S1 id}/download_self_declaration` into the address bar. | Redirects to the admin 404 page. **No** PDF is downloaded. |
| 2.3 | Flag **on**. Reload S1's Startup Detail page. | A **Download Self Declaration** button (PDF icon) appears in its own row **above** Backdoor Login / Print / Message. |
| 2.4 | Flag **on**. Open S1 in print view (click **Print**, or `/startup-detail/{S1 id}?printable=1`). | The printable page has no Self Declaration button (it hides action buttons). Print itself works as before. |
| 2.5 | Flag **on**, flag off again mid-session (developer flips it, then you reload). | Button disappears after reload; the direct URL goes back to 404 (2.2). |
| 2.6 | Flag on. Log in as B and open S1. | Button is visible (the page's own permissions decide who sees the page; the button follows the flag). Download works (4.1). |

## 3. Settings Management: the template and logo

Where to go for all of section 3: log in as A → top bar **Developer zone → Settings Management** (`/developer/settings_management?type=startup_grant_release_letter`) → left tab **Startup Grant Release Letter**.

| # | Do | Expected |
|---|---|---|
| 3.1 | Open the tab for the first time on a tenant. | Three fields: the logo uploader, the **Grant Release Letter template**, and a new **Startup Self Declaration Template** textarea, pre-filled with the self-declaration wording ("To / The Director / … / Sub: Self declaration / [x] I certify … / Notes: … / Representative Name / {{representative_name}} …"). The placeholder hint under it lists `{{representative_name}}, {{company_name}}, {{date}}`. |
| 3.2 | Compare the default text with `self.pdf`. | Same wording, including the original spellings ("financical", "subsidary", "benifits"). They match the government form and must **not** be "corrected". |
| 3.3 | Upload a logo (PNG) with **Select image**, click **Save settings**. Reload the page. | Success message "Settings were successfully updated."; the logo preview shows after reload. |
| 3.4 | Edit one word in the Self Declaration template (e.g. add " (test)" to the Sub line). Save. Reload. | The edited text is still there. The Grant Release Letter template is unchanged. |
| 3.5 | Reload the page several more times, and open another Settings tab and come back. | Your edit is **not** reset to the default (seeding never overwrites a saved value). |
| 3.6 | Paste template text copied from Word or Google Docs (line breaks from rich text). Save. Download the PDF (4.1). | Lines stay separate; nothing runs together on one line. |
| 3.7 | Log in as B (no Settings Management access) and try `/developer/settings_management?type=startup_grant_release_letter`. | Access refused / redirected, as for any other settings tab. |
| 3.8 | Restore the default wording at the end of testing (copy it from 3.1 or ask the developer). | Default text back for the following sections. |

## 4. Download: positive (happy path) cases

Where to go: log in as A, flag on, **Startup / MSME list → S1 → Startup Detail** (`/startup-detail/{S1 id}/details`), click **Download Self Declaration**.

| # | Do | Expected |
|---|---|---|
| 4.1 | Click **Download Self Declaration** on S1. | A file `startup-{id}-self-declaration.pdf` downloads (no new tab with an error text). The page stays on Startup Detail. |
| 4.2 | Open the PDF. | **One** A4 portrait page. |
| 4.3 | Check the top. | Logo at the top left (the one uploaded in 3.3), then bold "To", then The Director / Directorate of Information Technology / Govt. of Tripura / Indranagar, Agartala , Tripura, a blank gap, then bold "Sub:" followed by "Self declaration". |
| 4.4 | Check the five certification rows. | A rounded light-grey box with five rows separated by thin lines. Each row has a **blue square with a white tick** on the left and the full sentence justified to the right. Wording matches `self.pdf`. Rows wrap at the same words as `self.pdf` (row 1 ends "…has not / exceeded Twenty Five crore rupees"). |
| 4.5 | Check the Notes. | Small plum-coloured bold "Notes:" then the two sentences (Turnover Rs.25 Crores; Terms & Condition of the Tripura Start-Up Policy 2024). |
| 4.6 | Check the signature box. | Right-aligned rounded box with bold labels and plain values: **Representative Name** = S1 owner name ("mohan"), **Company Name** = S1 company ("Coder Group"), **Date** = today in `dd/mm/yyyy`. |
| 4.7 | Check the margins. | Equal left and right margins of about 5% of the page width each. Text does not touch or get cut at the page edge anywhere. |
| 4.8 | Compare the whole page next to `self.pdf`. | Same structure, spacing, fonts and wording. Only the values (name, company, date, logo artwork) differ. |
| 4.9 | Download the PDF twice for the same startup. | Both files identical except possibly the date if run across midnight. No error, no duplicate side effects. |
| 4.10 | Download for two different startups in a row (S1 then another). | Each PDF shows its **own** representative and company, no data carried over. |
| 4.11 | Print the PDF from the viewer (or Save as PDF). | Prints on one A4 page, nothing clipped. |

## 5. Download: edge cases and content variations

| # | Do | Expected |
|---|---|---|
| 5.1 | Download for **S-long**. | The long company name wraps inside the signature box on two or more lines. The box grows; text stays inside the box and on the page; still **one page**. |
| 5.2 | Download for **S-special** (`A&B <Tech> "Labs" O'Neil Pvt Ltd`, `Zoë Müller-Ñandi`). | The characters appear **literally as typed** (`A&B <Tech> "Labs"`), accents correct. No HTML is interpreted, no missing text, no broken layout. |
| 5.3 | Download for **S-blank** (empty company or owner name). | The blank value shows as a dash "—" (never an empty gap or the literal `{{company_name}}`). The PDF still downloads. |
| 5.4 | In the template, change `[x] ` to `[ ] ` on the second certification and save (3.4). Download. | That row shows an **empty bordered box** instead of the blue tick; the other four stay ticked. Restore after the test. |
| 5.5 | In the template, delete the whole `Notes:` block and save. Download. | PDF still downloads. The Notes section is simply absent; nothing else breaks. Restore after. |
| 5.6 | In the template, rename the line `Representative Name` to `Representative` and save. Download. | PDF still downloads without error. The signature box is not drawn separately (its text shows in the body). Restore after. |
| 5.7 | In the template, add a sixth `[x] I certify …` row and save. Download. | Six rows. Still renders correctly and on one page. Restore after. |
| 5.8 | In the template, add 25 extra lines of text and save. Download. | PDF downloads without error (it may run to two pages; that is acceptable). Restore after. |
| 5.9 | Remove the logo (leave the logo field empty / ask the developer to clear the setting). Download. | PDF downloads with no logo; the text starts a little higher. No error text. |
| 5.10 | Download with a logo that is a JPG, then a PNG. | Both appear. |
| 5.11 | Use `{{date}}` only once in the template, then change the system date on the day boundary (or ask the developer to confirm the format). | Date is today's date as `dd/mm/yyyy`, in the server timezone. |

## 6. Negative and security cases

| # | Do | Expected |
|---|---|---|
| 6.1 | Flag **off**, call the download URL directly (see 2.2). | 404 redirect. No file. |
| 6.2 | Log out. Paste the download URL in the address bar. | Redirected to the login page. No PDF. |
| 6.3 | Flag on. Log in as A. Open `/startup-detail/999999999/download_self_declaration` (an id that does not exist). | Admin 404 page. No PDF, no PHP error text. |
| 6.4 | Flag on. Open `/startup-detail/abc/download_self_declaration`. | 404 page. No PDF, no PHP error text. |
| 6.5 | Flag on. Log in as **P**. Download for **P-own**. | PDF downloads. |
| 6.6 | Flag on. Log in as **P**. Try the download URL for **P-other**. | **403** page. No PDF. |
| 6.7 | Flag on. As A, in the template put `<script>alert(1)</script>` and `{{company_name}}` in a line, save, download. | The script text appears as plain text in the PDF. No script runs anywhere. (Restore after.) |
| 6.8 | Flag on. Make the template empty (clear the textarea, save) and download. | The browser shows a plain text message "PDF generation failed: No self declaration template is configured yet (Settings Management > Startup Grant Release Letter)." instead of a file. The page does not white-screen. The developer sees the cause in `php_error.log`. Restore the template. |
| 6.9 | Tenant isolation: log in on tenant X's admin, download for a startup. Then compare with tenant Y. | Each tenant only sees its own startups, template and logo. A startup id from tenant X returns 404 on tenant Y's admin. |
| 6.10 | Click **Download Self Declaration** twice quickly. | Two identical downloads or the browser's duplicate prompt; no server error. |

## 7. Regression: things that must NOT change

| # | Do | Expected |
|---|---|---|
| 7.1 | Startup Detail → **Print**. | Opens the printable view exactly as before. |
| 7.2 | Startup Detail → **Message**, **Backdoor Login**, **Delete** (Developer role). | Behave as before (do not actually delete). |
| 7.3 | Startup Detail → Accept / Reject / Flag buttons on a pending startup (flag on and off). | Layout intact; the new button row does not push them off screen. |
| 7.4 | Application Detail (`/application-submission-detail/{id}`) → Download dropdown → **Download Grant Release Letter** (flag on). | Still downloads the Grant Release Letter with its own wording. Editing the Self Declaration template in 3.4 did **not** change it. |
| 7.5 | Application Detail → **Download as PDF**. | Unchanged. |
| 7.6 | Settings Management → other tabs (Branding, Notifications, Policies). Save one unrelated setting. | Saves normally; the two letter templates are unaffected. |
| 7.7 | Check the browser console on Startup Detail (F12 → Console). | No new JavaScript errors from the new button. |
| 7.8 | Responsive: shrink the browser to tablet and phone width on Startup Detail. | The new button wraps cleanly; no horizontal scroll caused by it. |

## 8. UAT scenarios (business sign-off, end to end)

Run these as the programme officer, in order, on a UAT tenant with the flag on.

| # | Scenario | Steps (where to go) | Acceptance |
|---|---|---|---|
| U1 | **Officer issues a self declaration for a recognised startup** | Log in → Startup / MSME list → search "Coder Group" → open the startup → click **Download Self Declaration** → open the PDF. | The PDF looks like the government form, carries the startup's real owner and company name and today's date, and can be printed and filed. |
| U2 | **Admin updates the government wording** | Developer zone → Settings Management → Startup Grant Release Letter → edit the Notes sentence → Save → open any startup → download. | The new wording appears in the next PDF without a deploy. |
| U3 | **Tenant branding** | Upload the tenant's logo in the same tab → download again. | The logo of the tenant appears at the top of the declaration. |
| U4 | **Partner scope** | Log in as a partner → open own startup → download; then try another partner's startup by URL. | Own: works. Other: access denied. |
| U5 | **Feature switched off** | Ask the developer to switch the flag off for the tenant → reload Startup Detail. | Button gone; Grant Release Letter also hidden (same switch). Switch back on after the test. |
| U6 | **Bulk sample** | Download the declaration for five different startups across approved and pending statuses. | Each shows its own name and company; none errors; all one page. |

## 9. Sign-off

| Section | Cases | Passed | Failed | Notes |
|---|---|---|---|---|
| 2 Gating | 2.1–2.6 | | | |
| 3 Settings | 3.1–3.8 | | | |
| 4 Positive | 4.1–4.11 | | | |
| 5 Edge | 5.1–5.11 | | | |
| 6 Negative / security | 6.1–6.10 | | | |
| 7 Regression | 7.1–7.8 | | | |
| 8 UAT | U1–U6 | | | |

Sign-off: QA (Ritu Raj) ______  Date ______   Product owner ______  Date ______

Known limits that are **not** defects: no audit-log row is written for a download; the date is the download date, not a stored declaration date; the five certifications are always ticked (fixed template text, not startup input); a very long template can span two pages.
