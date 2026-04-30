# Plan: Port Three mattpocock Skills + Add `parallax sync`

## Context

Two parallel additions:

**A. Port four skills** from [mattpocock/skills](https://github.com/mattpocock/skills) into Parallax's bundled templates: `diagnose`, `zoom-out`, `improve-codebase-architecture`, `ubiquitous-language`. The user prefers vendoring (controllable, stable) over upstream-tracking. `grill-me` is already adapted; not touching it.

**B. New `parallax sync` command** to push template updates (CONSTITUTION.md, skills, agents, hooks, settings.json) into already-initialized projects. Today the only path is rerunning `parallax init` in merge mode — works but couples to a fresh interview. `sync` decouples upgrades from initialization.

Decisions resolved with user: reuse merge mode (suffix conflicts as `.parallax.ext`, write merge guide), full template-derived scope, never touch CLAUDE.md/PARALLAX.md.

Note on `ubiquitous-language`: source lives at `skills/deprecated/ubiquitous-language/`. Mattpocock added it on 2026-04-28 and deprecated it the same day in favor of `grill-with-docs` (which couples glossary maintenance to an active grilling session). For Parallax it's a better fit *because* it's standalone — orthogonal to existing `grill-me`, single-file, no ADR/CONTEXT machinery to inherit.

---

## Part A — Port four skills

### A1. Per-skill spec

| Source | Target | Notes |
| --- | --- | --- |
| `engineering/diagnose/SKILL.md` | `src/parallax/templates/skills/diagnose.md` | ~150 lines. Strip "domain glossary"/"ADR" prose; replace examples that lean on Order/Customer with Hypothesis/Experiment framing. Cross-reference `/hypothesis` and `/test-integrity` in a one-line "see also". |
| `engineering/zoom-out/SKILL.md` | `src/parallax/templates/skills/zoom_out.md` | ~10 lines. Drop "domain glossary" reference (or soften to "the project's `UBIQUITOUS_LANGUAGE.md` if one exists"). Keep `disable-model-invocation: true`. |
| `engineering/improve-codebase-architecture/SKILL.md` + `LANGUAGE.md` | `src/parallax/templates/skills/improve_architecture.md` | Inline `LANGUAGE.md`'s glossary section (Module/Interface/Depth/Seam/Adapter/Leverage/Locality + deletion-test/interface-is-test-surface principles) into the SKILL body to keep flat-file convention. Drop `INTERFACE-DESIGN.md` reference. Drop CONTEXT.md/ADR coupling. **Set `disable-model-invocation: true`** — user-invoked only (heavyweight; would derail normal coding turns; deep-module pressure can hurt scientific code where the math IS the interesting part). Add a Parallax-specific preamble warning that for numerical/scientific code, "shallow" isn't always wrong — visibility of the algorithm often beats encapsulation when correctness depends on reading it. Keep textbook terms as-is (Ousterhout, Pragmatic Programmer); user explicitly wants "better science with better software engineering". |
| `deprecated/ubiquitous-language/SKILL.md` | `src/parallax/templates/skills/ubiquitous_language.md` | ~80 lines, single file, self-contained. Keep `disable-model-invocation: true`. Replace business-domain example dialogue (Order/Invoice/Customer) with science example (Hypothesis/Experiment/Measurement/Dataset). Keep `UBIQUITOUS_LANGUAGE.md` as the output filename — distinctive and matches Parallax's all-caps doc convention. |

### A2. Shared adaptation rules (apply to all four)

- Top-of-file attribution comment (HTML comment so it survives but stays out of rendered headers): `<!-- Adapted from github.com/mattpocock/skills (MIT). -->` (license confirmed permissive by user).
- Strip TS/JS-specific phrasing.
- Match Parallax tone: concise, no LLM-speak, no emojis (already in CLAUDE.md writing style).
- Substitute `${project_name}` only where it adds value (e.g., diagnose's "use the project's domain glossary" → "use `${project_name}`'s `UBIQUITOUS_LANGUAGE.md` if present"). Most files don't need it.
- For `diagnose` and `zoom-out`: where upstream references "domain glossary," route to the new `ubiquitous-language` skill so the four skills compose.

### A3. Registration

Edit `src/parallax/core/renderer.py:323` (`_SKILL_NAMES` list) to append: `"diagnose"`, `"zoom_out"`, `"improve_architecture"`, `"ubiquitous_language"`. The renderer's hyphen-conversion logic at `renderer.py:355` already handles `zoom_out` → `zoom-out/` etc.

### A4. Tests

- Add fixtures: each new skill gets a sanity-check assertion in `tests/test_core/test_renderer.py` confirming the file is rendered to `.claude/skills/<hyphen-name>/SKILL.md` with frontmatter intact.
- Add an integration check in `tests/test_cli/test_init.py` that the four new skills appear in the post-init output tree.
- No new tests for skill *content* — these are templates, not code.

### A5. Documentation

- Update `README.md` skill list (under "What exists"): add the four new skill names.
- Update `docs/toolkit.md` (referenced in README) with descriptions of each new skill — same per-skill blurb format already present.

---

## Part B — `parallax sync` command

### B1. Behavior

```
parallax sync [-t TARGET] [--dry-run]
```

1. Verify `target/PARALLAX.md` exists. If not, error: "Not a Parallax-managed project."
2. Load `target/.parallax/config.json` (see B3 below). If absent, error with remediation: "No persisted config. Re-run `parallax init -f` once to capture state, then sync." (Don't try to derive from existing files — too brittle for a sync semantic.)
3. Render the **sync subset** of templates (CONSTITUTION.md + skills + agents + hooks + settings.json), excluding CLAUDE.md and PARALLAX.md.
4. Run `classify_outputs`-style classification against the target. Three buckets:
   - **identical** — skip
   - **new** — write directly
   - **conflicting** — suffix as `.parallax.ext` (reusing `_suffix_path` at `renderer.py:415`)
5. If any conflicts: write `.parallax/merge-guide.md` (reusing `_write_merge_guide` at `renderer.py:458`) and print: "Run `parallax refine` to merge."
6. Print summary: `N new | M updated (suffixed) | K identical (skipped)`.
7. `--dry-run` flag prints the summary without writing.

### B2. Implementation

#### Renderer changes (`src/parallax/core/renderer.py`)

- Add `_render_sync_content(config: ProjectConfig) -> dict[str, str]` — like the existing `_render_all_content` at `renderer.py:382`, but excludes the CLAUDE.md and PARALLAX.md entries. Pure function, no I/O. Implement by extracting a helper that takes a list of "kinds" to include, then call it with `{"constitution", "skills", "agents", "hooks", "settings"}` for sync vs. the full set for init. Refactor `_render_all_content` to use the same helper to avoid duplication (CONSTITUTION principle 11).
- Add `_render_sync(config, target) -> MergeResult` — like `_render_merge` at `renderer.py:580`, but calls `_render_sync_content` and uses sync's "identical = skip, new = write, conflict = suffix" semantics. The merge-mode counterpart already has this exact shape; mostly a function rename + content-source swap. Reuse `_suffix_path`, `_write_merge_guide`, `MergeResult`.

#### CLI changes (`src/parallax/cli/__init__.py`)

- Add `@app.command("sync")` peer to `init`/`refine` (around line 230).
- Read `target/.parallax/config.json` via `ProjectConfig.from_json` (`config.py:74`).
- Call `_render_sync(config, target)`.
- Print summary using same style as init merge mode.

#### Persistent config (`src/parallax/core/config.py` + `cli/__init__.py`)

- Introduce `_CONFIG_REL = Path(".parallax") / "config.json"` (peer to existing `_CACHE_REL` at `cli/__init__.py:40`).
- After successful init (after refinement, before cache deletion at `cli/__init__.py:187`), write `config.to_json(target / _CONFIG_REL)`. This persists the snapshot for future syncs.
- `parallax config set token-tier` also updates `config.json` (one-line write of the new tier). Without this, the snapshot diverges from what's actually rendered in agent files, and the next `sync` would render with a stale tier. If `config.json` doesn't exist (legacy project), `config set` continues to work as today (regex-only path) and prints a notice that sync won't work until reinit.
- Migration story for legacy projects: documented in error message (B1 step 2).

### B3. Tests (`tests/test_cli/test_sync.py` — new file)

- `test_sync_requires_parallax_md` — error if PARALLAX.md missing
- `test_sync_requires_config_json` — error with remediation if `.parallax/config.json` missing
- `test_sync_writes_new_skill` — add a new entry to `_SKILL_NAMES`, sync writes it
- `test_sync_skips_identical` — pre-create matching content, sync reports "identical"
- `test_sync_suffixes_conflict` — pre-edit a skill file, sync writes `.parallax.md` and merge guide
- `test_sync_does_not_touch_claude_md` — pre-edit CLAUDE.md, sync leaves it alone
- `test_sync_does_not_touch_parallax_md` — same for PARALLAX.md
- `test_sync_dry_run` — `--dry-run` writes nothing, prints summary
- Renderer-level: `tests/test_core/test_renderer.py::TestRenderSyncContent` — confirms `_render_sync_content` excludes CLAUDE.md/PARALLAX.md and matches `_render_all_content` for everything else.
- Init-level: extend `tests/test_cli/test_init.py` to assert `.parallax/config.json` is written after success.

### B4. Documentation

- `README.md` Usage section: add `parallax sync` block.
- `README.md` "What's next" → move "Template versioning / migration" closer to "done" or remove (sync delivers the practical benefit).
- `docs/ROADMAP.md` — close out the sync entry if it exists; otherwise note it shipped.

---

## Critical files

- `src/parallax/core/renderer.py` — `_SKILL_NAMES` (line 323), add `_render_sync_content`, `_render_sync`, refactor `_render_all_content` to share helper with sync path
- `src/parallax/core/config.py` — no schema change; just used in new persistence path
- `src/parallax/cli/__init__.py` — new `sync` command, persist `config.json` after init success (~line 187), update `_set_token_tier` to also update `config.json`
- `src/parallax/templates/skills/` — four new files: `diagnose.md`, `zoom_out.md`, `improve_architecture.md`, `ubiquitous_language.md`
- `tests/test_cli/test_sync.py` — new
- `tests/test_cli/test_init.py` — extend to cover config.json persistence
- `tests/test_core/test_renderer.py` — add sync-content classifier tests
- `README.md`, `docs/toolkit.md` — update skill list and add `parallax sync` to Usage

## Reuse — existing functions/utilities

- `MergeResult` (`renderer.py:22`) — reuse as-is
- `_suffix_path` (`renderer.py:415`) — reuse for `.parallax.ext` suffixing
- `classify_outputs` (`renderer.py:425`) — reuse against sync content dict
- `_write_merge_guide` (`renderer.py:458`) — reuse to drop merge-guide.md
- `_render_merge` (`renderer.py:580`) — pattern to mirror for `_render_sync`
- `_REFINEMENT_PROMPT` / `_MERGE_REFINEMENT_PROMPT` (`refiner.py:14,36`) — `parallax refine` already auto-detects merge guide (`cli/__init__.py:252`) and switches prompts. Sync produces the same merge guide → refine flow works unchanged. **No refiner changes needed.**
- `ProjectConfig.to_json` / `from_json` (`config.py:66`, `:74`) — reuse for persistent snapshot
- `_MODEL_MAP` / `model_for_agent` (`renderer.py:195`) — already used by both renderer and `config set`; sync inherits

## Verification

Per CLAUDE.md "Plan Completion & Verification":

```bash
pixi run check                          # ruff + mypy --strict + pytest
pixi run test tests/test_cli/test_sync.py
pixi run test tests/test_cli/test_init.py
pixi run test tests/test_core/test_renderer.py
```

End-to-end manual smoke test:

```bash
# 1. fresh project gets new skills
mkdir /tmp/parallax-smoke && cd /tmp/parallax-smoke
parallax init -y
ls .claude/skills/                       # expect: ...diagnose, zoom-out, improve-architecture, ubiquitous-language
test -f .parallax/config.json            # expect: present

# 2. simulate template upgrade by editing a skill in place, then sync
echo "# user edit" >> .claude/skills/hypothesis/SKILL.md
parallax sync                            # expect: "1 updated (suffixed)" + merge guide
ls .claude/skills/hypothesis/            # expect: SKILL.md (user) + SKILL.parallax.md (template)
cat .parallax/merge-guide.md             # expect: hypothesis pair listed
parallax refine                          # auto-detects merge guide
parallax refine --done                   # cleanup

# 3. sync against legacy project (no config.json)
rm .parallax/config.json
parallax sync                            # expect: loud error with remediation
```

Then `/test-integrity` before commit (CLAUDE.md mandates this when tests are modified).

Then verify @README.md and docs/toolkit.md reflect the new skills + `parallax sync` command.

---

## Unresolved questions

None blocking. All decisions resolved:

- License: permissive, attribution comment in each ported file.
- `improve-codebase-architecture`: keep textbook terms; user-invoked only with science-code preamble warning against over-deepening.
- CONSTITUTION.md sync: same suffix-on-conflict as skills; `parallax refine` synthesizes.
- `config set` updates `config.json`: yes (keeps snapshot consistent with rendered agent files).
- `disable-model-invocation: true` on `zoom-out`, `ubiquitous-language`, and `improve-codebase-architecture`. `diagnose` allows auto-invocation (it's the natural response to "this is broken" / "debug this").
