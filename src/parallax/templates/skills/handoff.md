# /handoff -- Agent Handoff Summary

> Generate a structured handoff summary for ${project_name}.

## When to Use

Invoke `/handoff` at the end of a work session, before context gets too long, or when passing work to another agent/human.

## Output Format

Generate the following sections:

```markdown
## Handoff: [date or session identifier]

**Problem statement:** [1-2 sentences]

**What was investigated/attempted:**
- [bulleted list]

**Key findings:**
- [bulleted list]

**Current state:**
- What works: [list]
- What doesn't: [list]

**Recommended next steps:**
1. [prioritized list]

**Open questions:**
- [list]

**Relevant files/paths:**
- [list with brief descriptions]
```

## Rules

- Be concise but complete. Another agent should be able to continue without re-investigating.
- Include file paths for all code that was touched or is relevant.
- Flag any known issues or risks explicitly.
- If a hypothesis was being tested, include its current status.
