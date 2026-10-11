# SAN-1158 — Backend debug console.log calls leak passwords and live auth tokens

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1158
- **Repo:** sc-saas-backend · **Priority:** Urgent · **Assignee:** Nirmal Singh
- **Classification:** CODE_ERROR (leftover debug logging)

## Problem
Leftover `console.log` calls printed credentials to stdout, and from there to pm2/server logs and any log shipping:
1. `src/core/services/ses-email.service.ts:1103`: the admin/jury account-created email's `attributesToMap`,
   which includes the new account's plaintext password (non-SSO) and login email.
2. `src/modules/partner/partner.service.ts:789`: `getAdminConsoleUrl()` printed the partner user's live JWT.
3. `src/modules/conversations/conversations.service.ts:169-174`: printed each group-chat member's full user
   record and the `receiverUserToken` embedded in the chat email's authenticated link.

Found while drafting FA-009 (platform email stats).

## Fix
The three logging blocks were deleted (8 lines, 3 files); nothing else changed. A repo-wide `console.log` scan for
password/token/secret/credential/attributesToMap now finds only CometChat's static "Missing Username or Password" messages.

## Verification
- `tsc --noEmit` is clean.
- eslint's 4 errors in `ses-email.service.ts` are existing Prettier formatting issues around line 4737, unrelated to this change.
- No automated test: this change only removes logging.

## Follow-up (ops)
Values already logged remain in existing logs. Clear or restrict old backend logs, and ask the admins and jury
members created while (1) was live to change their passwords. JWTs from (2) expire with their token lifetime.

## Commit
sc-saas-backend `404c483c` (on `ai_native_setup`)
