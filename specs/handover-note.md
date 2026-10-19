# The handover note (SAN-1629)

Every move of a Linear issue to **In Review** carries a handover note, posted as a comment at the moment of the move. The review gate needs an input: the reviewer reads the note, checks what it claims, and writes what they checked. An issue moved to In Review without one is not ready for review.

## The shape

Three headings, always in this order, always present (write "none" rather than drop one).

```markdown
**Handover for review**

**Changed**
- <repo>: <file or behaviour>, commit `<sha>` on `<branch>`
- ...

**Verified**
- `<command or request>` → <result, pasted, not paraphrased>
- ...

**Open**
- <anything the reviewer must decide, check by hand, or knows is not done>
```

### Changed
What is different now, by repo: the files or the behaviour, and the commit that holds it with the branch it is on. If the work spans repos, one line per repo. If nothing is committed yet, say so; that is not ready for review.

### Verified
The evidence, pasted. A command and its output (`npm run gates` summary, `composer gates`, `php -l`, a test run), a request and its response (status code, the relevant part of the body), a screenshot link. "Tested, works" is not evidence. If a check could not be run (no DB access, no running app), name it here as not run, and repeat it under Open.

### Open
What the reviewer has to decide or do: product questions, manual checks that need production access, follow-up work deliberately left out, risks. "None" is a valid answer, but only if it is true.

## The reviewer's reply

The reviewer answers the note with a comment naming what they actually checked ("ran the curl in Verified on dev, got 403 as stated"; "read the diff in `<sha>`"). Then they move the issue to Done, or back to In Progress with the reason. Nobody reviews their own handover.

## Example

```markdown
**Handover for review**

**Changed**
- sc-saas-backend: `conversations.service.ts` no longer logs the group-chat login link; new test `src/core/logging/no-credential-console-logs.spec.ts`. Commit `03272a21` on `ai_native_setup`.

**Verified**
- `npm run gates` → lint 0, test 0, test-floors 0, build 0, "=> passed"
- `git grep -n "console.log(chatPageUrl)" origin/ai_native_setup` → no match

**Open**
- Not deployed yet: reaches dev on the next "Build now" of the dev backend job.
- Purging old pm2 logs needs server access (SAN-1559 checklist).
```

## Where it is enforced

- `/bug-fix` (`.claude/commands/bug-fix.md`) and `spec-implementer` (`.claude/agents/spec-implementer.md`) post this note whenever they move an issue to In Review.
- The Linear issue template "Handover note" carries the same three headings for people writing it by hand.
- The Friday review samples two In Review moves at random and checks the Verified section has pasted evidence.
