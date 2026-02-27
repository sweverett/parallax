# Field-Test Protocol

How to field-test Parallax against a real (or realistic) scientific project.

## Purpose

Automated tests validate that Parallax generates correct output. Field-testing validates that the generated output is *useful* -- that the conventions, agents, skills, and hooks actually improve a real scientific workflow.

## What automated tests cover vs. what field-testing catches

| Aspect | Automated tests | Field-testing |
|---|---|---|
| Template rendering correctness | Yes | -- |
| No unsubstituted vars | Yes | -- |
| Hook script execution (stdin/stdout) | Yes | -- |
| Agent model selection per tier | Yes | -- |
| Generated CLAUDE.md quality/usefulness | -- | Yes |
| Skill instructions actually guide Claude | -- | Yes |
| Hook false positive rate | -- | Yes |
| Agent effectiveness at real tasks | -- | Yes |
| Interview question clarity | -- | Yes |
| Workflow friction (too many prompts, bad defaults) | -- | Yes |
| Missing conventions for a domain | -- | Yes |

## Phases

### Phase 1: Init validation (30 min)

1. Run `parallax init -t <target>` with a realistic project config
2. Verify all generated files exist and look reasonable
3. Read CLAUDE.md, PARALLAX.md, CONSTITUTION.md -- are instructions clear?
4. Check agent frontmatter -- correct models for chosen tier?
5. Check hook scripts -- do they reference correct paths?
6. Run `parallax refine` workflow -- does refinement improve output?
7. Run `parallax refine --done` -- are comment blocks cleanly stripped?

### Phase 2: Workflow exercise (1-2 hrs)

1. Open Claude Code in the initialized project
2. Run `/session-start` -- does it orient the agent correctly?
3. Run `/hypothesis` -- does it produce a well-structured hypothesis?
4. Trigger the hypothesis-explorer agent -- does it investigate usefully?
5. Run `/experiment` -- does the manifest structure make sense?
6. Make a test edit that should trigger test_guard -- does it block?
7. Edit a .py file -- does lint_check provide useful ruff feedback?
8. Run `/handoff` -- is the summary useful for a future session?
9. Stop Claude Code -- does stop_check remind about uncommitted work?

### Phase 3: Edge cases (30 min)

1. `parallax init -y` -- are defaults reasonable?
2. `parallax init -f` on an already-initialized project -- clean overwrite?
3. Change token tier post-init with `parallax config set token-tier 5x` -- agents updated?
4. Project with no units, no JAX, no git prefix -- are conditional sections correctly absent?
5. Very long project summary / science requirements -- any truncation?
6. Domain with special characters (hyphens, numbers) -- renders correctly?

### Phase 4: Document findings

For each phase, record:
- **Worked as expected**: brief note
- **Friction/confusion**: describe what was unclear
- **Missing feature**: what the workflow needed but Parallax didn't provide
- **Bug**: incorrect behavior with reproduction steps

File findings as GitHub issues or add to ROADMAP.md.

## Candidate test project types

| Domain | Key features exercised |
|---|---|
| Astrophysics pipeline (photometric redshifts) | Units, JAX, large data, hypothesis-driven |
| Bioinformatics (sequence analysis) | No JAX, custom libraries, reproducibility-critical |
| Machine learning experiment tracker | JAX likely, rapid iteration, many hypotheses |
| Climate model analysis | Units, large data, literature-heavy |
| Pure software engineering (Parallax itself) | Meta-bootstrap, no units, CI-heavy |

Pick a project type that exercises the most features. Astrophysics or climate science recommended for first field test (exercises units, JAX, hypothesis workflow).
