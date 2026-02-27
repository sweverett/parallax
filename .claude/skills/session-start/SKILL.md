---
name: session-start
description: Bootstrap a new Parallax dev session. Reviews recent handoffs, MEMORY.md, and current project state.
disable-model-invocation: true
---

# /session-start -- Session Onboarding

> Bootstrap a new work session by reviewing previous handoffs, semantic memory, and current state.

## When to Use

Invoke `/session-start` at the beginning of a new Parallax development session.

## Instructions

1. **Read recent handoffs.** Find and read the 3 most recent files in `docs/sessions/` (by filename sort). Most recent is primary; older ones provide trajectory. If <3 exist, read all.
2. **Check semantic memory.** MEMORY.md is auto-loaded but verify it matches codebase state. Flag contradictions.
3. **Read strategic context.** Read `docs/VISION.md` and `docs/ROADMAP.md`. Read the most recent file in `docs/plans/` (by filename sort -- highest `NNN` prefix). Map current state against the roadmap: what's done, what's next, what's blocked.
4. **Audit current state.** Run `pixi run check`. Review recent `git log --oneline -20`. Check ROADMAP.md and README.md for currency.
5. **Parallel exploration (when warranted).** For broad-scope sessions (multiple areas to check, many recent changes), consider using parallel subagents to speed up onboarding -- e.g. checking recent changes, test coverage, doc staleness concurrently. Use judgment; skip this for small/focused sessions.
6. **Critically evaluate the handoffs.** Don't parrot their recommendations. Challenge priorities if the codebase state suggests different next steps. Note anything the handoffs missed or got wrong.
7. **Synthesize and present:**
   - What was done last session
   - Where we stand now (test/lint/typecheck status, open branches, uncommitted work)
   - Strategic alignment: where current state sits relative to ROADMAP layers, what the next logical milestone is
   - Recommended next steps (may differ from handoff's recommendations -- explain why)
   - Unresolved questions requiring human input
8. **Wait for human direction** before starting work.

## Rules

- Be critical. The handoff is a starting point, not a directive.
- If `pixi run check` fails, that takes priority over any planned work.
- If docs are stale, flag it explicitly.
- If MEMORY.md contradicts current codebase state, flag it and propose corrections.
- Keep the synthesis concise -- bullet points, not paragraphs.
