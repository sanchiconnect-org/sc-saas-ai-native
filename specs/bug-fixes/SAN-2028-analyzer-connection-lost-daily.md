---
id: SAN-2028
title: "AI analyzer ConnectionResetError now bursts daily: SAN-1980 fix plan never applied"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-2028
sentry: [AI-STARTUPS-ANALYZER-7]
repos: [ai-analyzer]
related: [SAN-1980]
commit: none — repo not cloned in this workspace, fix plan only
created: 2026-10-26
updated: 2026-10-26
---

# SAN-2028: analyzer pool still hits dropped idle connections

## Investigation
* 78 events in total, 28 of them in 14 days. It now bursts 9-10 events every day in production on `sc-doc-ai`:
  * 10-21 06:58:44
  * 10-22 07:58:47 (trace `6e3ac3ed…`)
  * 10-23 06:41:17 (trace `be9c0bf2…`)
* The stack is unchanged: `sqlalchemy/pool/base.py:375 _close_connection` → aiomysql `ensure_closed` → `writer.drain()` → reset. `mechanism: logging`, logger `AsyncAdaptedQueuePool`.
* Triggering span: `SELECT … FROM batches WHERE run_id=%s AND batch_number=%s` (on 10-21 it was the `UPDATE batches`).
* The release tag is empty (`ai-startups-analyzer@`), so the deployed build can't be identified.

## Root cause
Same as SAN-1980: MySQL drops idle pooled connections, and the pool then fails while closing them. SAN-1980 was closed with only a fix plan; no code shipped.

## Fix
Not applied, because `ai-startups-analyzer` is not cloned in this workspace. The plan:
* `pool_pre_ping=True` and a `pool_recycle` below MySQL's `wait_timeout` on `create_async_engine`.
* Retry the `batches` writes once when `connection_invalidated` is set.
* Set a Sentry release tag.

## Blast radius / existing-flow impact
Pre-ping adds one cheap round-trip per connection checkout. No API change; the analyzer is a leaf node.

## Verification
Pending the code change. After deploy: no burst for ~7 days, and a release tag on later events.
