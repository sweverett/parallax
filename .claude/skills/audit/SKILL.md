---
name: audit
description: Structured audit of the Parallax codebase. Run periodically or before major milestones.
disable-model-invocation: true
---

# /audit -- Project Audit

> Structured audit of the Parallax codebase.

## When to Use

Invoke `/audit` periodically or before major milestones to check project health.

## Checks

Perform each check and report findings:

1. **Code review:** Bugs, concerns, anti-patterns, security issues in `src/parallax/`.
2. **Test gaps:** Untested features, weak assertions, missing edge cases in `tests/`.
3. **Doc staleness:** Do README.md, CLAUDE.md, ROADMAP.md, VISION.md match current code? Are references valid?
4. **Dependency health:** Outdated or vulnerable dependencies in pyproject.toml/pixi.toml.
5. **Architecture:** Does code match the 3-layer design in VISION.md? Any drift?
6. **Scientific rigor:** Are hypotheses documented? Results reproducible? Assumptions stated?

### Parallax-Specific Checks

- ROADMAP.md: are completed items checked off? Are open questions still relevant?
- README.md: does "Current Status" section reflect reality?
- `pixi run check` passes cleanly (lint, typecheck, test).
- Session summaries in `docs/sessions/` are up to date.
- No TODO markers in production code or skills.

## Output Format

```markdown
## Audit: [date]

### Critical
- [findings that need immediate attention]

### Warning
- [findings that should be addressed soon]

### Info
- [observations and suggestions]

### Summary
[1-2 sentence overall assessment]
```

## Rules

- Check @CONSTITUTION.md principles against actual practice.
- Flag any tests that appear to have relaxed tolerances.
- Verify reproducibility claims (are environments locked? versions pinned?).
- Be specific: include file paths, line numbers, concrete evidence.
- Run `pixi run check` as part of the audit.
