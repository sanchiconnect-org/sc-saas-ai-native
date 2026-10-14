---
description: Scaffold a new spec (feature or module) from the template.
argument-hint: feature <linear-id> | module <repo>/<module>
---
$ARGUMENTS
- "feature <linear-id>": before delegating, ask the user two things in one question (SAN-1579: a spec is a milestone in an existing project, not a new project):
  1. **Which existing Linear project** the spec belongs to. Suggest `Enhancement` (the default home) or the owning program's project, from `list_projects` (team: Sanchiconnect). A new project only if they explicitly want one **and** give a lead and a target date, **and** the work is about five issues or more. Otherwise say why not and suggest a milestone instead.
  2. **Who to assign** the spec's issues to (one person for the whole spec).

  Then delegate to the spec-author subagent for that Linear issue, passing `project: <name>` and `assignee: <name>` (and `lead:` + `target date:` if a new project was agreed). spec-author creates a milestone named "<id> — <title>" in that project and puts the per-repo issues in it.
- "module <repo>/<module>": copy specs/module.spec.template.md to <repo>/src/<module>/module.spec.md, fill what you can infer from code, leave TODOs.
