# SAN-1148 — Intermittent "Direct access is not allowed" flash on tenant custom domains

- **Linear:** https://linear.app/sanchiconnect/issue/SAN-1148
- **Repo:** sanchiconnect-saas-tenants · **Assignee:** Nirmal Singh
- **Classification:** CODE_ERROR

## Problem
`isRegisteredHostname()` only checked an in-memory snapshot of `cors_domains`, refreshed on a blind 30 s timer.
Two of the three writers to that table are PHP processes using raw SQL. The only "refresh now" path is a best-effort
HTTP push that silently does nothing on timeout or misconfiguration. So a newly registered domain could get a 403 for up
to 30 s (longer across replicas) before healing.

## Fix (`48abc7f`)
- **Cache miss:** `cors-domains.service.ts` falls back to a live, case-insensitive DB read (new repository method) before
  rejecting. The common cached path is unchanged, with no extra DB calls.
- **Separate bug:** `refreshCache()` never lowercased stored domains, so a mixed-case domain always failed the comparison.
- `domain-resolver.service.ts` was adjusted to match.

## Verification
- New and updated jest specs: `cors-domains.service.spec.ts`, `cors-domains.repository.spec.ts`,
  `domain-resolver.service.spec.ts`.

## Commit
sanchiconnect-saas-tenants `48abc7f` (on `ai_native_setup`)
