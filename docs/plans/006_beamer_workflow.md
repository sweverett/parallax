# 006: Beamer Presentation Workflow

## Goal

Strengthen presentation-writer agent, manuscript-reviewer agent, and latex-guide skill
to encode a complete Beamer presentation workflow with structured behaviors that go
beyond vanilla Claude Code prompting.

## What Parallax adds over pure Claude Code

- **presentation-writer agent** -- outline-first workflow, compile-after-every-change, auto-split dense frames, latex-guide on errors
- **manuscript-reviewer agent** -- auto-detects Beamer, checks slide density/narrative arc/timing/citations, severity-ranked output
- **latex-guide skill** -- auto-invoked on LaTeX errors, Beamer-specific coverage (metropolis, speaker notes, tikz, overlays)
- **/manuscript-review skill** -- lighter user-invoked checklist (no agent spawn)

## Changes

### presentation-writer.md (agent)
- Explicit numbered workflow: outline -> approval -> draft -> compile -> density check -> final compile
- "Show outline and wait for approval before proceeding"
- "Compile after every change" (not just after adding frames)
- Self-check density: split frames with >6 bullets or full sentences
- Speaker notes section with `\note{}` usage
- Flag missing visuals with `% TODO` comments

### manuscript-reviewer.md (agent)
- Expanded workflow with presentation-specific checks inline (density thresholds, timing estimates, narrative arc, visual hierarchy)
- Explicit output format: `[SEV:level] [file:line] description. Fix: recommendation.`
- Compilation failures marked severity:critical

### latex-guide.md (skill)
- Beamer issues table (was bullet list): overfull, fragile, token errors, blank frames, animations, themes
- Metropolis theme section: setup, customization, pdflatex vs XeLaTeX gotchas
- Speaker notes section: pgfpages setup, handout mode
- Animation/overlay reference: pause, only, onslide, uncover, alert, itemize incremental
- TikZ in frames section
- No changes to non-Beamer sections

### manuscript-review.md (skill)
- No changes needed -- already covers plan requirements

## Verification

```bash
pixi run check   # lint + format + typecheck + tests
```

All 207 tests pass. No code changes to renderer or tests needed -- template content changes only.
