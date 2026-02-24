# Plan: Add Custom Agent Definitions + Token Tier to `parallax init`

## Context

Claude Code now natively supports custom agent definitions (`.claude/agents/name.md`), git worktrees for agents (`isolation: "worktree"`), model selection per agent (`model: haiku|sonnet|opus`), and skill memory (`memory: project`). These features create a natural "Layer 1.5" for Parallax — shipping pre-built scientific agents alongside the existing skills/hooks.

This plan also captures the full overlap/synergy analysis as design context for future Layer 2/3 decisions.

---

## Skills vs Agents: The Mental Model

**Skills** = recipes injected into the current conversation. Teach Claude *how* to do something.
- User invokes with `/hypothesis`; Claude auto-invokes when relevant
- Run **inline** in current context window (shared, no isolation)
- Think: **methodology**

**Agents** = separate Claude instances with own context window, tools, permissions, model.
- Claude delegates via Task tool; user can also request directly
- **Isolated context** — fresh window, can run in git worktrees, can use cheaper models
- Can have skills preloaded (agent gets the methodology + operational constraints)
- Think: **specialized workers**

**Composition:** hypothesis-explorer agent preloads /hypothesis skill = methodology (skill) + operational constraints (agent: read-only, haiku, worktree isolation).

---

## Scientific Hierarchy: Hypothesis > Experiment

A **hypothesis** is a falsifiable claim ("adding caching reduces query time by 50%").
An **experiment** is a procedure that tests a hypothesis (write benchmark, run with/without cache, compare).

One hypothesis can spawn multiple experiments (different conditions, replication, parameter sweeps). Experiments are subordinate to hypotheses.

This shapes agent roles:
- **hypothesis-explorer**: investigate/research to formulate or evaluate a hypothesis (pre-experiment, evidence gathering)
- **experiment-runner**: execute a specific test of a hypothesis (create test scripts, run them, record results)
- **result-validator**: audit the rigor of both hypothesis formulation and experiment execution

---

## Overlap / Synergy Analysis

### Layer 1 (current) — Zero redundancy, pure synergy
Parallax generates content (CLAUDE.md, skills, hooks, settings.json). Claude Code executes it. No runtime overlap.

### Layer 2 (planned) — Partial overlap in worktrees
- **Git worktree plumbing**: Claude Code handles natively. Do NOT rebuild.
- **SQLite hypothesis tracking**: No native equivalent. Needed long-term for structured queries, reproducibility metadata, permanent scientific records. Short-term: skill `memory: project` as lightweight proxy.
- **Subagent orchestration**: Claude Code handles mechanics (Task tool). Parallax defines the scientific workflows.

### Layer 3 (future) — Major overlap with Agent Teams
- Agent Teams = multi-agent coordination, shared task lists, peer-to-peer comms
- Each teammate = full Claude instance. Too expensive for Pro/5x users.
- Parallax Layer 3: **token-efficient scientific coordination** via subagents (cheaper models). Teams as optional power-user mode.

### Future notes (not for this plan)
- **PreCompact hook**: promising for auto-saving hypothesis state before context compression. Needs dedicated design/brainstorming session.
- **Claude Code plugin**: could ship as `.claude/plugins/` package. Complicates structured interviews (plugins are static). Revisit when plugin system matures.

---

## Implementation Plan

### 1. Add `token_tier` to ProjectConfig

**File: `src/parallax/core/config.py`**

```python
TokenTier = Literal["pro", "5x", "20x", "api"]
```
Add `token_tier: TokenTier` to ProjectConfig. Add to validation set. Default: `"pro"`.

### 2. Add `custom_agent_description` to ProjectConfig

**File: `src/parallax/core/config.py`**

Add `custom_agent_description: str` (can be empty). No `generate_agents` boolean — core agents are always generated when skills are generated (that's the point of Parallax).

### 3. Add token tier interview question

**File: `src/parallax/core/interview.py`**

Phase A, after generate_hooks:
```
Token usage tier? [pro/5x/20x/api]
Context: Controls default model selection for generated agents.
  pro  — conservative: haiku exploration, sonnet validation
  5x   — balanced: sonnet exploration, opus validation
  20x  — generous: opus for most tasks
  api  — unconstrained: opus everywhere
Default: pro
```

With `--yes`: defaults to `"pro"`. Also expose as CLI flag: `parallax init --token-tier 5x`.

### 4. Add custom agent interview question

**File: `src/parallax/core/interview.py`**

Phase B (after key_libraries, only when not `--yes`):
```
Describe a custom agent (or leave blank to skip):
Context: Define a project-specific agent beyond the core scientific ones
  (hypothesis-explorer, experiment-runner, literature-reviewer, result-validator).
  Describe its purpose and what it should do. Parallax wraps it in a
  generic agent definition; the auto-refinement step polishes it.
  Example: "data-pipeline-validator -- checks ETL outputs for schema drift and NaN propagation"
```

Editor-based input. If non-empty, generates `.claude/agents/custom.md` with a generic frontmatter wrapper + the user's description as the body + a refinement comment block in CLAUDE.md telling Claude to review and improve the custom agent definition on first session.

### 5. Create agent templates

**New directory: `src/parallax/templates/agents/`**

Four core agents. Template variables (`${explorer_model}` etc.) are `string.Template` substitutions resolved at render time in Python — no env vars.

**`hypothesis_explorer.md`** — Read-only evidence gathering
```yaml
---
name: hypothesis-explorer
description: Investigate a hypothesis by searching code, tests, results, and data for supporting/refuting evidence.
model: ${explorer_model}
isolation: worktree
tools: [Read, Glob, Grep, Bash, WebSearch, WebFetch]
disallowedTools: [Edit, Write, NotebookEdit]
skills: [hypothesis]
---
Investigate a hypothesis in an isolated worktree. Do not modify any files.

Primary search targets (in priority order):
1. **Test results and outputs** — test logs, benchmark data, CI artifacts
2. **Experiment scripts and notebooks** — existing experimental procedures and their results
3. **Data files and logs** — raw outputs, processed results, error logs
4. **Source code** — implementation details relevant to the hypothesis
5. **Documentation** — prior hypotheses, session summaries, negative results

Report findings as:
- **Evidence for**: [specific findings supporting the hypothesis]
- **Evidence against**: [specific findings refuting it]
- **Gaps**: [what evidence is missing or untested]
- **Confidence**: high / medium / low (with justification)
- **Recommended next steps**: [specific experiments or investigations to run]

Negative results are valuable — document them with equal rigor.
Reference @CONSTITUTION.md principles throughout.
```

**`experiment_runner.md`** — Create and execute tests of a hypothesis
```yaml
---
name: experiment-runner
description: Design and execute an experiment to test a hypothesis. Creates test scripts, runs them, records results.
model: ${runner_model}
isolation: worktree
tools: [Read, Glob, Grep, Edit, Write, Bash]
skills: [experiment]
---
Design and execute an experiment in an isolated worktree to test a specific hypothesis.

Before starting, record:
- Hypothesis being tested (link to hypothesis ID if available)
- Git ref (commit hash) and branch
- Environment details (Python version, key package versions)
- Parameters and configuration

Execution steps:
1. **Create test scripts or validation code** specific to this hypothesis.
   Write new test files, benchmarks, or analysis scripts — don't just run existing tests.
2. **Run the experiment** and capture all output.
3. **Record raw results** — numbers, logs, errors, timing data.
4. **Assess outcome**: supported / refuted / inconclusive, with specific evidence.
5. **Document unexpected observations** — these often lead to new hypotheses.

Output follows the /experiment skill manifest format.
If inconclusive, specify exactly what additional evidence would resolve it.
```

**`literature_reviewer.md`** — Read-only literature/reference search
```yaml
---
name: literature-reviewer
description: Search for and summarize relevant literature, papers, and references for the project's scientific domain.
model: ${reviewer_model}
tools: [Read, Glob, Grep, Bash, WebSearch, WebFetch]
disallowedTools: [Edit, Write, NotebookEdit]
---
Search for relevant literature, papers, documentation, and references related
to the project's scientific domain: ${domain}.

Search targets:
1. **Academic papers** — arxiv, journal databases, preprints
2. **Technical documentation** — library docs, API references, method descriptions
3. **Existing codebase references** — cited papers, referenced methods, bibliography files
4. **Related implementations** — open-source projects tackling similar problems

Report findings as:
- **Relevant papers/refs**: [title, authors, year, key finding, relevance to current work]
- **Methods described**: [techniques that could apply to current hypothesis/experiment]
- **Contradictions or caveats**: [findings that conflict with assumptions]
- **Gaps in literature**: [what hasn't been studied or is under-explored]

Prioritize recency and direct relevance. Flag foundational vs. incremental contributions.
```

**`result_validator.md`** — Read-only scientific rigor audit
```yaml
---
name: result-validator
description: Validate scientific rigor of results, experiments, or implementations. Read-only critical review.
model: ${validator_model}
tools: [Read, Glob, Grep]
disallowedTools: [Edit, Write, Bash, NotebookEdit]
skills: [audit]
---
Validate the scientific rigor of results or implementation. Be constructively critical.

Check for:
1. **Reproducibility**: can this be reproduced from the recorded state alone?
2. **Statistical soundness**: are claims supported by sufficient evidence?
3. **Methodology transparency**: are all assumptions, approximations, and limitations documented?
4. **Test coverage**: are edge cases and failure modes tested?
5. **Unit consistency**: dimensional analysis correct? (if applicable)
6. **Hypothesis-experiment linkage**: does the experiment actually test the stated hypothesis?

Challenge assumptions. Flag concerns. A well-documented concern now prevents a retraction later.
Reference @CONSTITUTION.md principles throughout.
```

### 6. Model selection by token tier (pure Python, no env vars)

**File: `src/parallax/core/renderer.py`**

Python dict mapping `(agent_name, token_tier) -> model_string`:

| Agent | pro | 5x | 20x | api |
|---|---|---|---|---|
| hypothesis-explorer | haiku | opus | opus | opus |
| experiment-runner | sonnet | sonnet | opus | opus |
| literature-reviewer | haiku | sonnet | opus | opus |
| result-validator | sonnet | opus | opus | opus |

`render_agent()` looks up the model, substitutes into template via `string.Template.safe_substitute()`. Output file has concrete model name baked in (e.g., `model: haiku`).

### 7. Add agent rendering to renderer

**File: `src/parallax/core/renderer.py`**

Extends existing pattern (same as `render_skill()`):
- `_AGENT_TEMPLATES = importlib.resources.files("parallax.templates.agents")`
- `_AGENT_NAMES = ["hypothesis_explorer", "experiment_runner", "literature_reviewer", "result_validator"]`
- `render_agent(name, config)` — load template, substitute model per token_tier + project_name
- `render_custom_agent(config)` — wrap user description in generic frontmatter, write as `.claude/agents/custom.md`

Update `_output_paths()` and `render_project()`:
- Core agents always generated when `config.generate_skills=True` (agents require skills)
- Custom agent generated when `config.custom_agent_description` is non-empty
- Output path: `.claude/agents/name.md` (flat files — agent convention, not subdirectories)

Template filenames: underscores (`hypothesis_explorer.md`) for Python import compat.
Output filenames: hyphens (`hypothesis-explorer.md`) matching Claude Code convention.

### 8. Add `memory: project` to /hypothesis and /experiment skill templates

**Files: `src/parallax/templates/skills/hypothesis.md`, `experiment.md`**

Add `memory: project` to frontmatter of both. Gives cross-session persistence via `.claude/memory/`. Short-term proxy for hypothesis tracking; SQLite still planned for Layer 2 when we need structured queries and permanent scientific records.

### 9. Add /session-start to generated skills

**File: `src/parallax/templates/skills/session_start.md`**

Generalized version of Parallax's own `/session-start`. Bootstraps new sessions by reading latest handoff from `docs/sessions/`, checking project state.

Add `"session_start"` to `_SKILL_NAMES` in renderer. Guarded by `generate_skills`.

### 10. Auto-refinement: invoke Claude CLI at end of init

**Files: `src/parallax/cli/__init__.py`, new `src/parallax/core/refiner.py`**

After `render_project()` completes, `parallax init` auto-invokes Claude Code CLI to run a synthesis/refinement pass. This eliminates the "half-finished until first session" state.

**Flow:**
1. `render_project()` writes all template files (with refinement comment blocks as before)
2. New `run_refinement(target_dir)` function spawns:
   ```
   claude -p "<refinement prompt>" --cwd <target_dir>
   ```
3. Refinement prompt instructs Claude to:
   - Read all generated files (CLAUDE.md, PARALLAX.md, CONSTITUTION.md, skills, agents)
   - Synthesize sections for internal consistency (cross-references, terminology, tone)
   - If custom agent exists: reformat `.claude/agents/custom.md` — infer proper name, description, tools, model from user's description; rename file to match agent name
   - Strip refinement comment blocks when done
   - Report what was changed
4. If `claude` CLI not found or fails: warn user, leave refinement blocks intact, print instructions to run manually. Not a hard failure.

**Graceful degradation:**
```python
def run_refinement(target: Path) -> bool:
    """Invoke Claude CLI for synthesis. Returns True if successful."""
    if not shutil.which("claude"):
        typer.echo("Warning: 'claude' CLI not found. Run refinement manually.")
        return False
    # subprocess.run(["claude", "-p", REFINEMENT_PROMPT, "--cwd", str(target)])
```

**Refinement prompt** stored as a constant or template in `src/parallax/core/refiner.py`. Kept separate from templates since it's not user-facing output. Prompt design: general instructions for tone/consistency across most files, but very specific and detailed about Parallax architecture, file relationships, scientific workflow design, and hypothesis/experiment hierarchy — the domain knowledge Claude won't have without explicit context.

**`--skip-refine` flag:** Added to `parallax init`. Off by default (refinement runs). When set, leaves refinement comment blocks intact and prints instructions to run manually later.

**README.md:** Document Claude Code CLI as prerequisite + expected setup flow including refinement step.

**README.md requirement:** Add Claude Code CLI as a dependency/prerequisite in the install section.

### 11. Add `parallax config` command

**File: `src/parallax/cli/__init__.py`**

New CLI command for post-init config changes without full reinitialization:
```
parallax config set token-tier 5x
```

Subcommand-style (`parallax config set <key> <value>`) to anticipate future config options. For token-tier: reads existing `.claude/agents/*.md` files, updates `model:` field in frontmatter based on new tier mapping, writes back. Only touches agent model lines — no other files affected.

Future keys: branch-prefix, etc. For now, only token-tier implemented. Document in README.md.

### 12. Update tests

- **Config tests**: new fields (token_tier, custom_agent_description), validation of TokenTier values
- **Interview tests**: new questions, --yes defaults, --token-tier flag
- **Renderer tests**: agent output paths, agent content, model selection per tier, custom agent generation
- **Refiner tests**: mock subprocess to verify claude CLI invocation, graceful degradation when missing
- **Config command tests**: token-tier update rewrites agent model lines correctly
- **E2E tests**: full init with agents, verify files exist with correct models
- **Integration tests**: validate agent frontmatter YAML structure

### 13. Update docs

- README.md: add agents to generated output list, token tier to CLI usage, Claude Code CLI as prerequisite
- CLAUDE.md: add `.claude/agents/` to directory structure
- ROADMAP.md: mark agent generation complete, note worktree plumbing deferred to Claude Code native, update Layer 2 notes

---

## Files to modify

| File | Change |
|---|---|
| `src/parallax/core/config.py` | Add TokenTier, token_tier, custom_agent_description |
| `src/parallax/core/interview.py` | Add token tier question + custom agent question |
| `src/parallax/core/renderer.py` | Add agent rendering, model mapping, output paths |
| `src/parallax/cli/__init__.py` | Add `--token-tier` flag, `parallax config` command |
| `src/parallax/templates/skills/hypothesis.md` | Add `memory: project` to frontmatter |
| `src/parallax/templates/skills/experiment.md` | Add `memory: project` to frontmatter |
| `tests/test_core/test_config.py` | New field validation tests |
| `tests/test_core/test_interview.py` | New question tests |
| `tests/test_core/test_renderer.py` | Agent rendering tests |
| `tests/test_cli/test_e2e.py` | Agent file existence tests |
| `tests/test_cli/test_init.py` | Updated init output, --token-tier flag tests |
| `tests/test_integration/test_generated_output.py` | Agent structure validation |
| `README.md` | Generated output list, usage |
| `CLAUDE.md` | Directory structure |
| `docs/ROADMAP.md` | Layer 1/2 status updates |

## New files

| File | Purpose |
|---|---|
| `src/parallax/templates/agents/__init__.py` | Package init for importlib.resources |
| `src/parallax/templates/agents/hypothesis_explorer.md` | Explorer agent template |
| `src/parallax/templates/agents/experiment_runner.md` | Runner agent template |
| `src/parallax/templates/agents/literature_reviewer.md` | Literature search agent template |
| `src/parallax/templates/agents/result_validator.md` | Validator agent template |
| `src/parallax/templates/skills/session_start.md` | Session bootstrap skill template |
| `src/parallax/core/refiner.py` | Claude CLI invocation for auto-refinement |

---

## Verification

1. `pixi run check` — all tests pass, lint clean, mypy --strict clean
2. `parallax init -t /tmp/test-proj` — verify agents/ + skills/ generated, default pro tier models
3. `parallax init -t /tmp/test-5x --token-tier 5x` — verify model escalation in agent files
4. `parallax init -t /tmp/test-minimal -y` — verify defaults (pro, core agents, no custom agent)
5. Manual: open Claude Code in generated project dir, confirm agents discoverable

---

## Resolved during planning

- **Literature-reviewer**: no preloaded skills. General-purpose (novelty checks + hypothesis-scoped searches). User/Claude provides context per invocation.
- **`parallax config set` validation**: loud error if `.claude/agents/` missing. Informative message: "No agents found. Run `parallax init` first."
- **`${domain}` in literature-reviewer**: full domain string from interview.
- **Model hierarchy rationale**: `pro` tier optimizes for volume economics (haiku explorer = run many cheap). `5x` tier optimizes for judgment quality (opus explorer = hypothesis quality determines everything downstream). Both valid for their contexts.

## Unresolved questions

- None blocking implementation. Refinement prompt content will need iteration during development.
