---
name: handoff
description: Generate a structured handoff summary for Parallax development sessions.
disable-model-invocation: true
---

# /handoff -- Agent Handoff Summary

> Generate a structured handoff summary for Parallax development sessions.

## When to Use

Invoke `/handoff` at the end of a work session, before context gets too long, or when passing work to another agent/human.

## Instructions

1. **Promote to semantic memory if warranted.** If this session produced stable knowledge (implementation details, debugging patterns, gotchas) not already in CLAUDE.md or MEMORY.md, propose additions to MEMORY.md. Session-specific details (what was done, next steps) stay in the session file only.
2. Write the handoff summary to `docs/sessions/YYYY-MM-DD_short-description.md` (use today's date, append `_2` if file exists).
3. Include all sections from the output format below.
4. Be concise but complete -- another agent should continue without re-investigating.

## Output Format

```markdown
# Session: [date] -- [short description]

## What Was Done
- [bulleted list of completed work]

## Key Decisions
- [architectural choices, design tradeoffs, rejected alternatives]

## Current State
- What works: [list]
- What doesn't: [list]
- Test status: [pixi run check result summary]

## Next Steps
1. [prioritized list]

## Open Questions
- [unresolved items needing human input]

## Relevant Files
- [file paths with brief descriptions of changes]
```

## Self-Review Pass

After writing the initial draft, re-read it critically and check for:

1. **Unverified claims.** Did you assert something works without evidence? Flag it as untested.
2. **Missing context.** Could a fresh agent pick up from this alone? What would they waste time rediscovering?
3. **Gaps in "What doesn't work."** "Nothing known" is almost always wrong. Think about what wasn't tested, what was deferred, what assumptions went unchecked.
4. **Test intent shifts.** If tests were modified, did the *meaning* of the test change, not just the assertion values?
5. **Upstream continuity.** Is there prior session context (plans, earlier sessions) that this handoff assumes but doesn't reference?

Update the draft with findings, then present to the user.

## Rules

- **Memory boundary:** MEMORY.md = stable facts learned through experience. Session files = temporal context. CLAUDE.md = rules and conventions. When in doubt, session file -- promote later.
- Include file paths for all code that was touched or is relevant.
- Flag any known issues or risks explicitly.
- If a hypothesis was being tested, include its current status.
- Run `pixi run check` before writing the summary to capture current state.
- Verify ROADMAP.md and README.md are current before finalizing.
