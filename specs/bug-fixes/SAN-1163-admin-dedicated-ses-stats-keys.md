# SAN-1163 — Admin: dedicated SES_STATS_* keys for SES stats lookups

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1163
- **Repo:** sc-saas-admin · **Type:** Improvement · **Priority:** Medium · **Assignee:** Nirmal Singh · **Related:** SAN-1155, SAN-1157

## Problem
The admin's SES v2 client (Request Stats → `getMessageInsights`) used the shared `spa_amazon_*` keys, the same keys as S3.
On dev those keys belong to IAM user `SanchiSaasDevS3`, which lacks `ses:GetMessageInsights`, so every lookup returned
AccessDenied. The backend stats job already supported dedicated `SES_STATS_*` keys (SAN-1155).

## Change
- `config/config.php`: new constants `ses_stats_access_key_id`, `ses_stats_secret_access_key` and `ses_stats_region`,
  read from the env names the backend uses (`SES_STATS_ACCESS_KEY_ID` / `SES_STATS_SECRET_ACCESS_KEY` /
  `SES_STATS_REGION`). Each falls back to its `spa_amazon_*` counterpart when unset or empty.
- The SES clients in `modules/broadcast_messages/details.php`, `modules/partners/broadcast/details.php` and
  `modules/email_logs/list.php` use them, and so does the `regionTried` value in their error responses.
  The S3 clients are unchanged.

## Setup
Dev: IAM user `SanchiSaasDevSES` needs an access key (not the SMTP password, which only works over SMTP) and an
inline policy allowing `ses:GetMessageInsights`. Set `SES_STATS_*` in both the admin and backend `.env`.
Deployments without `SES_STATS_*` keep using `spa_amazon_*` exactly as before.

## Verification
`php -l` clean on all 4 files; no `//` comments added. Not tested against live SES from here.

## Commit
sc-saas-admin `4dcabdc5` (on `ai_native_setup`)

## Reverted (2026-10-01)
Removed at the user's request, together with the backend's `SES_STATS_*` support from SAN-1155:
- **Admin:** SES clients (broadcast details, partner broadcast details, Email Logs) use `spa_amazon_*` again.
- **Backend:** the `syncBroadcastEmailStats` job uses `AMAZON_*`; the `sesStats` config, Joi keys and
  getters were deleted.

The IAM user behind those keys must allow `ses:GetMessageInsights`. `SES_STATS_*` entries left in a `.env`
are now ignored.
