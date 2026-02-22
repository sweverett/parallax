# /handoff -- Agent Handoff Summary

> Generate a structured handoff summary for Parallax development sessions.

## When to Use

Invoke `/handoff` at the end of a work session, before context gets too long, or when passing work to another agent/human.

## Instructions

1. Write the handoff summary to `docs/sessions/YYYY-MM-DD_short-description.md` (use today's date, append `_2` if file exists).
2. Include all sections from the output format below.
3. Be concise but complete -- another agent should continue without re-investigating.

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

## Rules

- Include file paths for all code that was touched or is relevant.
- Flag any known issues or risks explicitly.
- If a hypothesis was being tested, include its current status.
- Run `pixi run check` before writing the summary to capture current state.
- Verify ROADMAP.md and README.md are current before finalizing.
