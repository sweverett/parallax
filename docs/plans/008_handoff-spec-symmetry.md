# Plan: Symmetric handoff/session-start contract

## Context

Reader/writer asymmetry in Parallax's session-handoff design. Current state:

- **Reader** (`session_start.md` skill, line 17): "Find and read the 3 most recent files in `docs/sessions/` (by filename sort)."
- **Writer** (`handoff.md` skill): defines content sections only; never specifies filename, storage path, or that the agent should *write a file at all*.
- **PARALLAX.md template** (`Agent Handoff Format`, lines 35–45): content-only spec; no path, name, tracking, or trigger.

The reader spec assumes a writer convention that was never written down. In deployed projects this leaks: agents either follow the spec strictly and grab wrong files, or silently fall back to `ls -t` (mtime) and the spec rots. Either failure is silent — violates CONSTITUTION.md principle 8 ("loud errors over silent failures").

External feedback recommends: write down the writer's contract (filename + storage + tracking + trigger), make the reader self-check by failing loudly on non-conforming files, and tighten the existing `/handoff` skill to actually write the file.

**Asymmetric stance taken here:** writer-side is rigid (single filename rule, file-write step enforced); reader-side is adaptive (tries the conformant path, falls back gracefully, surfaces drift as an observation rather than a blocking error). The contract belongs to the writer; the reader inherits whatever exists and shouldn't refuse to start a session over filename hygiene.

User decisions captured (asked before drafting):
- Generated projects: `docs/sessions/` **untracked** by convention.
- Filename: prefer descriptive distinct topics; `_2` suffix is a fallback for collisions only — no timestamps.
- Skill placement: tighten existing `/handoff` (no new `/session-end`).
- Scope: templates + skills only. No migration helper — `parallax sync` propagates the changes.

## Changes

### 1. `src/parallax/templates/parallax_md.tpl`

Replace the current `Agent Handoff Format` section (lines 35–45) with content-spec + new writer-side spec.

```markdown
## Agent Handoff Format

When ending a session or handing off to another agent:

### Content

- Problem statement (1-2 sentences)
- What was investigated/attempted
- Key findings (bulleted)
- Current state (what works, what doesn't)
- Recommended next steps
- Open questions
- Relevant files/paths

### Filename and storage

- **Path:** `docs/sessions/<filename>`
- **Filename:** `YYYY-MM-DD_<topic>.md`
  - Date is the day the handoff is written, ISO format, prefix position.
  - Topic is short kebab- or snake-case identifying the work (e.g. `merge-mode`, `pixel-conv-cleanup`).
  - Date prefix ensures `ls docs/sessions/ | sort -r` returns chronological newest-first.
- **Collisions:** prefer a more specific distinct topic over numeric suffixes. If two sessions on the same day genuinely cover the same topic, fall back to `_2`, `_3`, etc.
- **Tracking:** by default, do not git-track handoffs. They are agent working notes, not project source-of-truth — do not stage or commit them. Whether to `.gitignore` `docs/sessions/` is up to the project; the rule is "don't add by default," not "must be ignored."
- **Trigger:** write a handoff at the end of any session that produced commits, unresolved decisions, or open questions for the next session. Skip only for trivial sessions with no continuity value.
```

### 2. `src/parallax/templates/skills/handoff.md`

Add a "Write to file" step and reference the PARALLAX.md filename rule. Concrete edits:

- After the current `## Output Format` block (line 42), insert:

  ```markdown
  ## Write to File

  Write the completed handoff to `docs/sessions/YYYY-MM-DD_<topic>.md` per the filename rule in PARALLAX.md (`Agent Handoff Format > Filename and storage`). Use today's date as ISO prefix; pick a short distinct kebab- or snake-case topic. If the file already exists, prefer a more specific topic over `_2` suffixing.

  Do not `git add` or commit the handoff — these are agent working notes, not project source-of-truth.
  ```

- Update `## Rules` (lines 56–61) — add bullet:
  - "Always write the handoff to `docs/sessions/` per PARALLAX.md naming rule. Do not just display it in chat."

### 3. `src/parallax/templates/skills/session_start.md`

Reader stays adaptive — the writer is the contract holder, the reader is robust to drift. Replace line 17 with:

```markdown
1. **Read recent handoffs.** Find the 3 most recent handoffs in `docs/sessions/`. The project convention is `YYYY-MM-DD_<topic>.md` — run `ls docs/sessions/ | sort -r | head -3` for the conformant case (descending alphabetical = chronological newest-first by date prefix). If files do not follow the convention, fall back to mtime (`ls -t docs/sessions/ | head -3`) and note the inconsistency in your synthesis at step 5 so the user can decide whether to rename. Do not block the session on it. Most recent is primary; older ones provide trajectory. If <3 exist, read all.
```

Key shift from feedback's recommendation: reader does not loudly error on non-conforming files. It tries the spec'd path first, falls back to mtime gracefully, and surfaces the inconsistency as an *observation* in the session synthesis — not as a blocking failure. The writer-side spec (item 1, item 2) is where rigidity lives; the reader is built to tolerate drift in the corpus it inherits.

### 4. `CLAUDE.md` (Parallax dev project root)

Coherency fix: lines 134–141 of `Episodic Memory` currently say "Multiple sessions per day: append `_2` suffix" as the default. Update to match the new convention:

- Primary: distinct descriptive topic per session — collisions should be rare.
- Fallback: `_2`, `_3` suffix only when topics genuinely overlap.

Also add one sentence: "If you find non-conforming filenames in `docs/sessions/`, flag and rename rather than tolerate."

This project's existing 10 session files already conform (`YYYY-MM-DD_<topic>.md`); no migration needed here.

### 5. Tests

Existing assertions in `tests/test_core/test_renderer.py:197-198`, `tests/test_integration/test_generated_output.py`, `tests/test_cli/test_e2e.py` only check string presence — won't break.

**Add two new regression assertions** to lock in the load-bearing strings of the new spec (cheap, prevents silent template drift):

a. In `tests/test_core/test_renderer.py::test_session_start_render` (line 195), add:
   ```python
   assert "sort -r" in out          # conformant-path command for reader
   ```

b. Add a new sibling test `test_handoff_render_contains_writer_rule`:
   ```python
   def test_handoff_render_contains_writer_rule(self) -> None:
       out = render_skill("handoff", make_config())
       assert "docs/sessions/" in out                      # storage path
       assert "YYYY-MM-DD" in out                          # filename rule reference
   ```

c. Add an assertion to whatever test renders PARALLAX.md (search `parallax_md` or `Agent Handoff Format` in `test_renderer.py`):
   ```python
   assert "Filename and storage" in out                    # new subsection landed
   ```

If no test currently renders `parallax_md.tpl` directly, add a minimal one alongside the existing skill render tests.

That's it — three small assertions across two test functions plus one possibly new one. They protect: reader knows the sort command, writer knows the path, PARALLAX.md ships the new subsection.

## Critical Files

- `src/parallax/templates/parallax_md.tpl` — extend Handoff Format section
- `src/parallax/templates/skills/handoff.md` — add file-write step + path rule
- `src/parallax/templates/skills/session_start.md` — explicit sort + flag-the-violation
- `CLAUDE.md` (project root) — coherency update on `_2` fallback rule
- `tests/test_core/test_renderer.py` — optional regression assertions

## Verification

1. `pixi run check` — ruff, mypy, pytest baseline.
2. `parallax init -t /tmp/parallax-handoff-spec-test -y --skip-refine` and inspect:
   - `/tmp/parallax-handoff-spec-test/PARALLAX.md` contains `Filename and storage` subsection with `YYYY-MM-DD_<topic>.md`.
   - `.claude/skills/handoff/SKILL.md` contains the `Write to File` block and `docs/sessions/` path.
   - `.claude/skills/session-start/SKILL.md` contains `sort -r | head -3` and the "flag the violation" clause.
3. `parallax sync -t /path/to/existing/parallax-project --dry-run` — confirm the three updated templates show as changes (not no-ops).
4. Manual coherency: read the three rendered files end-to-end as a fresh agent would. The writer rule must be findable from `/handoff` alone (no need to cross-reference PARALLAX.md to know *where* to write). The session-start skill must read cleanly without sounding alarmist about non-conforming files.

## Unresolved Questions

None — gitignore is documentation-only (no auto-patch, no enforcement); numeric fallback stays tolerated; test assertions are in.
