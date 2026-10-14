---
description: Read a Linear issue and kick off a feature spec from it.
argument-hint: <linear-id>
---
Read Linear issue `$ARGUMENTS` (description + comments) via the Linear MCP connector.

If the Linear connector is not authenticated (no `mcp__claude_ai_Linear__*` issue tools available, only the `authenticate` tool), STOP and tell me to connect Linear from Claude's connector settings — do not guess the issue contents.

Otherwise, summarize the issue in one paragraph, then run `/spec-new feature $ARGUMENTS`, which first asks me for the existing Linear project (the spec becomes a milestone in it, SAN-1579) and the assignee, then delegates to the spec-author subagent to produce specs/features/$ARGUMENTS-<slug>.spec.md with status: draft. Report the resulting spec path and its Open questions so I can resolve them before approval.
