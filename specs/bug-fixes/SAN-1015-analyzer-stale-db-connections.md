# SAN-1015 — AI analyzer: "Exception closing connection" / "Connection lost" on idle pooled MySQL connections

- **Linear:** SAN-1015 (AI-STARTUPS-ANALYZER-7, 50 events)
- **Repo:** ai-startups-analyzer (outside the workspace folder, `C:\Users\Lenovo\Desktop\Work\ai-startups-analyzer`) · **Assignee:** Aman kabra · **Classification:** CODE/CONFIG

## Problem
MySQL had already dropped an idle pooled connection, and `AsyncAdaptedQueuePool` tried to close or reuse the dead aiomysql socket
(`ConnectionResetError: Connection lost`). Handled, but logged to Sentry.

## Fix
`api/app/core/database.py`: `create_async_engine(..., pool_pre_ping=True, pool_recycle=DB_POOL_RECYCLE)` with
`DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))`. `echo=True` is unchanged (it logs every SQL statement in production; worth
turning off separately).

## Needs a check
`DB_POOL_RECYCLE` must stay below MySQL's `wait_timeout` / any proxy idle timeout, or the recycle does not help.

## Contract impact
None. Internal pool configuration; called only by sc-saas-admin and never calls back. No API, flag, tenancy or auth change.

## Verification
`py_compile` OK. No automated tests exist in that repo and SQLAlchemy is not installed locally, so it was not run against a database.

## Commit
ai-startups-analyzer `77ab299`, pushed to the new remote branch `ai_analyizing_new_updates_aman` (its deploy branch is not known). Not deployed.
