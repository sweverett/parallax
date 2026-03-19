# Beamer Presentation Workflow: Parallax + Claude Code

## What Parallax adds over pure Claude Code

Pure Claude Code: you prompt, it edits .tex, you compile, you review manually, repeat.

Parallax adds:
- **`presentation-writer` agent** — specialized Beamer agent that outlines frames before writing, enforces one-idea-per-frame, compiles after every change, auto-invokes `latex-guide` on errors
- **`manuscript-reviewer` agent** — read-only reviewer that auto-detects Beamer mode and checks slide density, narrative arc, timing (~2min/frame), citation grounding, LaTeX hygiene. Returns numbered issues with severity levels.
- **`latex-guide` skill** — auto-invoked (no slash command needed). Covers Beamer-specific issues: overfull frames, fragile content, theme conflicts, animation, BibTeX integration.
- **`/manuscript-review` skill** — lighter user-invoked review checklist (no agent spawn)
- **CLAUDE.md / PARALLAX.md** — project conventions baked in so every Claude Code session starts informed

Key difference: instead of you being the only reviewer, the manuscript-reviewer agent gives structured feedback (severity-ranked, with fix recommendations) that you'd otherwise do mentally. And presentation-writer has Beamer-specific constraints baked in (outline-first, compile-after-write) that vanilla Claude Code won't enforce.

---

## Setup

```bash
mkdir ~/repos/claude-code-sci-talk && cd ~/repos/claude-code-sci-talk
git init
parallax init -t . --token-tier 5x --skip-refine
# --skip-refine: skip CLAUDE.md auto-refinement (overkill for a talk repo)
# --token-tier 5x: gives opus to writing/review agents (noticeably better than sonnet)
```

Answer the interview. Domain ~ "scientific computing", summary ~ whatever fits.

After init, relevant files:
```
.claude/agents/presentation-writer.md
.claude/agents/manuscript-reviewer.md
.claude/skills/latex-guide/SKILL.md
.claude/skills/manuscript-review/SKILL.md
```

---

## Workflow

### 1. Create Beamer scaffold

Ask Claude Code (normal session, not an agent):
```
Create main.tex with documentclass beamer, metropolis theme, title/author/date. Empty for now.
```

Or do it yourself. Either way, commit the skeleton.

### 2. Draft with presentation-writer agent

```
@presentation-writer "Outline and draft a Beamer presentation about [topic]. Sections: [list]. Keep frames minimal."
```

What the agent does differently than vanilla Claude Code:
- Writes a frame outline first, shows you, then fills content
- One idea per frame (will split dense frames)
- Runs `pdflatex`/`latexmk` after writing — you see compilation result immediately
- If compilation fails, `latex-guide` skill auto-activates with Beamer-specific fixes
- Won't fabricate figures — flags missing visuals instead

### 3. Fine-tune with Claude Code

Switch back to normal Claude Code for granular edits:
```
"Move the hooks frame before the MCP frame"
"Add speaker notes to frames 3-7"
"Replace the bullet list on frame 5 with a tikz diagram"
```

`latex-guide` still auto-activates on any LaTeX errors here too.

### 4. Review with manuscript-reviewer agent

```
@manuscript-reviewer "Review my presentation"
```

Auto-detects Beamer (finds `\begin{frame}`), then checks:
- Slide density (too much text per frame?)
- Visual hierarchy
- Narrative arc (does the talk flow?)
- Timing estimate (~2min/frame)
- Citation completeness (broken `\cite{}` keys?)
- LaTeX warnings/errors

Output: numbered list of issues, each with severity (critical / major / minor / suggestion) and a concrete fix recommendation. **Read-only** — won't modify files.

### 5. Fix and re-review

Apply feedback via Claude Code or presentation-writer, then `@manuscript-reviewer` again. Repeat.

For quick spot-checks without spawning the full agent:
```
/manuscript-review
```

---

## Iteration loop

```
@presentation-writer  -->  claude code  -->  @manuscript-reviewer
      (draft)            (fine edits)          (review)
                                                  |
                              <--- fix feedback ---
```

Commit after each meaningful milestone so you can revert.

---

## Useful commands

```bash
latexmk -pdf main.tex          # compile
latexmk -pdf -pvc main.tex     # compile + auto-recompile on save (live preview)
git diff --stat                 # see what changed
```

---

## Tips

- **Commit after each section.** Agents make big changes; version control is your undo.
- **Run reviewer early.** Don't wait until "done" — catch structural issues while rewriting is cheap.
- **Give presentation-writer bullet points.** The more structure in your prompt, the better the first draft. Outline > vague description.
- **Use Claude Code for surgery, agents for bulk.** Agent for drafting 10 frames; Claude Code for tweaking one frame's layout.
- **`/manuscript-review` vs `@manuscript-reviewer`**: skill = quick checklist in current session. Agent = full isolated review with compilation check.
