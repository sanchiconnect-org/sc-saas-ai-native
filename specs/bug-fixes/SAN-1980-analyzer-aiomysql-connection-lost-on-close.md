---
id: SAN-1980
title: "ConnectionResetError: Connection lost while the SQLAlchemy pool closes dead aiomysql connections (AI-STARTUPS-ANALYZER-7)"
type: bug-fix
status: done
linear: https://linear.app/sanchiconnect/issue/SAN-1980
sentry: [AI-STARTUPS-ANALYZER-7]
repos: [ai-analyzer]
related: [SAN-1927]
commit: none — fix plan only, ai-startups-analyzer not cloned locally
created: 2026-10-22
updated: 2026-10-22
---

# SAN-1980: the analyzer's DB pool hands out connections MySQL has already dropped

## Investigation (from Sentry only)
* **Event:** `ConnectionResetError: Connection lost` in `asyncio/streams.py _drain_helper`, message `Exception closing connection <AdaptedConnection <aiomysql.connection.Connection …>>`.
  * Stack: `sqlalchemy/pool/base.py:375 _close_connection` → `aiomysql.py:114 close` → `aiomysql/connection.py:350 ensure_closed` → `writer.drain()` → reset.
  * `handled: yes`, `mechanism: logging`, logger `sqlalchemy.pool.impl.AsyncAdaptedQueuePool`. It is SQLAlchemy's own error log line, not an exception that reached a request.
  * Server `sc-doc-ai`, CPython 3.12.3, uvicorn `app.main:app`, environment production, release tag empty (`ai-startups-analyzer@`).
* **Shape of the burst:** the 9 recent events are all at 2026-10-21 06:58:44 UTC, in one trace (`278611ea…`), each on a **different** connection object. The span in that trace is the DB op `UPDATE batches SET status=%s, updated_at=now() WHERE batches.id = %s` (batch status update in scoring).
* **History:** 59 events since 2026-09-02, always in bursts of 9-10 on single days: 09-02, 09-11, 09-25, 09-26, 09-30, 10-21 (plus 1 on 09-22). Status regressed.
* **Which connection:** the DB driver (aiomysql), not an LLM-provider HTTP connection and not a client disconnect. Every frame is the SQLAlchemy pool closing an aiomysql socket.
* **DB-pressure correlation:** none at that time. No other project raised a DB error between 06:00 and 08:00 UTC on 2026-10-21. The "Too many connections" issues (SC-SAAS-ADMIN-5, SC-SAAS-TENANTS-ADMIN-4) are from ~2026-10-21 20:00 UTC, about 13 hours later.

## Root cause (inferred, not confirmed in code)
* The pool keeps idle connections. During a quiet period MySQL (or a proxy/NAT in between) drops them: `wait_timeout`, a server restart, or an idle-socket reset.
* The next checkout (here the batch-status UPDATE) gets a dead socket and SQLAlchemy sees a disconnect. On a disconnect it **invalidates the whole pool**, closing every pooled connection. Each close tries to write to an already-reset socket and logs `Exception closing connection` at error level, so one invalidation gives 9-10 Sentry events (≈ the pool size).
* So the noise is the invalidation. The real effect is the one statement that hit the dead connection. Whether that UPDATE failed (leaving a batch status stale) or was retried cannot be seen from Sentry; the triggering exception was not captured as its own event. [UNVERIFIED]
* Likely missing in the engine config: `pool_pre_ping=True` and/or a `pool_recycle` below MySQL's `wait_timeout`. [UNVERIFIED — repo not cloned; check `create_async_engine(...)`.]

## Fix plan (needs the repo cloned to implement)
1. In the `create_async_engine(...)` call: `pool_pre_ping=True` (tests each connection on checkout, replaces a dead one transparently) and `pool_recycle=` a value below the server's `wait_timeout` (e.g. 1800 s, or lower if RDS `wait_timeout` is lower; read it with `SHOW VARIABLES LIKE 'wait_timeout'`).
2. Check the batch-status write paths (`UPDATE batches SET status…`) handle `sqlalchemy.exc.DBAPIError` with `connection_invalidated=True` by retrying once on a fresh connection, so a batch is not left in a stale status.
3. Optionally, raise `sqlalchemy.pool` logging to CRITICAL in the Sentry logging integration (or `ignore_logger`) **only after** 1 is in, so the close-noise does not hide a real problem.
4. Set a real release tag in the Sentry init (the release is empty today, so regressions can't be tied to a deploy).
* Do not change the thesis timeout or the thread pool here; that is SAN-1927 (In Review), a separate issue.

## Blast radius / existing-flow impact
* `pool_pre_ping` adds one lightweight round trip per checkout; no API or contract change, no change for sc-saas-admin (the only caller).
* Leaf service: nothing downstream.

## Verification
* Sentry only: issue page, the 9 events of 2026-10-21, the trace, a per-day count over 90 days, and a cross-project error search for 06:00-08:00 UTC that day. No code read or run.

## Open
* Clone `ai-startups-analyzer` to implement and confirm the engine config.
* Check whether any batch was left in a wrong status around 2026-10-21 06:58 UTC (analyzer `batches` table).
* Sentry assignee on the issue is Aman.

## Related
SAN-1927 (analyzer thesis timeout, In Review, unrelated mechanism).
