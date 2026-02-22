# /session-start -- Session Onboarding

> Bootstrap a new work session by reviewing previous handoff and current state.

## When to Use

Invoke `/session-start` at the beginning of a new Parallax development session.

## Instructions

1. **Read the latest handoff.** Find and read the most recent file in `docs/sessions/` to pick up previous context.
2. **Audit current state.** Run `pixi run check`. Review recent `git log --oneline -20`. Check ROADMAP.md and README.md for currency.
3. **Critically evaluate the handoff.** Don't parrot its recommendations. Challenge priorities if the codebase state suggests different next steps. Note anything the handoff missed or got wrong.
4. **Synthesize and present:**
   - What was done last session
   - Where we stand now (test/lint/typecheck status, open branches, uncommitted work)
   - Recommended next steps (may differ from handoff's recommendations -- explain why)
   - Unresolved questions requiring human input
5. **Wait for human direction** before starting work.

## Rules

- Be critical. The handoff is a starting point, not a directive.
- If `pixi run check` fails, that takes priority over any planned work.
- If docs are stale, flag it explicitly.
- Keep the synthesis concise -- bullet points, not paragraphs.
