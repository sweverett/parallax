# Layer 2 Design — Scientific State Engine

Iterative research document. Not yet ready for implementation — future sessions should inspect, critique, and iterate on open questions before building.

## Vision

Layer 2 adds **persistent scientific state** to Parallax. The core workflow:

1. User converses with Claude → collaborative investigation formulation
2. Investigations refined into concrete tasks with success/failure criteria
3. Tasks dispatched as agents in git worktrees (Claude Code native)
4. Results written to SQLite DB (persistent, cross-agent readable)
5. Reviewer agent synthesizes evidence across tasks
6. Structured report for human → human decides next cycle

**Human conducts. Agents execute. DB persists. Skills structure.**

## Decisions Made

| Question | Decision | Rationale |
|---|---|---|
| Data model levels | **3: Investigation → Task → Run** | Runs are "loose" — not all tasks need multiple runs, but abstracting execution from design handles failures and param variation |
| Investigation types | **Generalized with type column** | `type IN ('hypothesis','exploration','feature','literature','custom')`. Single schema, single CLI, single agent infrastructure. Type determines review criteria. |
| Hierarchy | **Parent-child tree** (parent_id FK) | Low cost (one column), enables progressive decomposition. Most investigations are top-level. |
| DB role | **Source of truth** for scientific state | Session files (`docs/sessions/`) are completely separate — dev workflow episodic memory, not experiment tracking |
| DB location | **`.parallax/state.db`, git-ignored** | No binary in git. `parallax export` dumps to JSON for checkpointing/sharing. `parallax import` rebuilds from export. |
| Conductor | **Human drives, agents support** | Constitution #5. Skills structure interaction, agents handle grunt work. No autonomous orchestrator. |
| DB interface | **Python API + CLI wrapper + auto-summary** | `parallax.db.api` (testable core) → CLI (agent/human interface via Bash) → `.parallax/state.md` (read-only view for agents using Read tool) |
| Session files | **Unchanged, separate concern** | `docs/sessions/*.md` = dev episodic memory. DB = scientific investigation state. No conflation. |

## What Claude Code Handles (Don't Rebuild)

- Git worktrees (`isolation: worktree`) — agent plumbing
- Agent spawning (Task tool) — delegation mechanics
- Tool restrictions (`tools:`, `disallowedTools:`) — already configured
- Model selection (`model:` per agent) — token tier maps this
- Cross-session skill memory (`memory: project`) — Layer 2 replaces this for investigations

## Generalized Framework

The key insight: hypothesis testing, data exploration, feature development, and literature review share the same structural pattern — a top-level question, concrete procedures to address it, and execution attempts. Different types, same infrastructure.

| Generic | Hypothesis | Exploration | Feature Dev | Literature |
|---|---|---|---|---|
| Investigation | Hypothesis | Research question | Feature request | Review question |
| Task | Experiment | Analysis | Implementation | Search/synthesis |
| Run | Execution | Search iteration | Build attempt | Query attempt |

## Architecture: 3-Layer DB Interface

```
┌──────────────────────────────────────────────────┐
│  Claude Code Agents / Skills                     │
│  (via Bash tool → CLI, or Read tool → state.md)  │
├──────────────────────────────────────────────────┤
│  parallax CLI (typer)                            │
│  parallax investigation create/list/show/update  │
│  parallax task create/list/show/update           │
│  parallax run create/list/show/update            │
│  parallax note add/list                          │
│  parallax export / parallax import               │
├──────────────────────────────────────────────────┤
│  parallax.db.api (Python functions)              │
│  create_investigation(), update_task(), ...       │
│  Auto-regenerates .parallax/state.md on writes   │
├──────────────────────────────────────────────────┤
│  SQLite (.parallax/state.db, git-ignored)        │
│  WAL mode for concurrent access                  │
└──────────────────────────────────────────────────┘
```

## Schema (Revised)

```sql
-- Investigations: top-level questions/goals
CREATE TABLE investigations (
    id INTEGER PRIMARY KEY,
    type TEXT NOT NULL DEFAULT 'hypothesis'
        CHECK (type IN ('hypothesis','exploration','feature','literature','custom')),
    name TEXT NOT NULL,
    statement TEXT NOT NULL,      -- what are we trying to answer/do?
    rationale TEXT,               -- why do we expect this / why investigate?
    success_criteria TEXT,        -- measurable outcome if supported/achieved
    failure_criteria TEXT,        -- measurable outcome if refuted/failed
    status TEXT NOT NULL DEFAULT 'proposed'
        CHECK (status IN ('proposed','active','concluded','archived')),
    outcome TEXT                  -- for concluded: supported/refuted/inconclusive/completed/abandoned
        CHECK (outcome IS NULL OR outcome IN ('supported','refuted','inconclusive','completed','abandoned')),
    parent_id INTEGER REFERENCES investigations(id),
    tags TEXT,                    -- JSON array of string tags for informal grouping
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks: concrete procedures linked to an investigation
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    investigation_id INTEGER NOT NULL REFERENCES investigations(id),
    name TEXT NOT NULL,
    description TEXT,             -- what will be done
    test_plan TEXT,               -- step-by-step procedure
    status TEXT NOT NULL DEFAULT 'proposed'
        CHECK (status IN ('proposed','active','concluded')),
    outcome TEXT
        CHECK (outcome IS NULL OR outcome IN ('supported','refuted','inconclusive','completed','failed')),
    evidence TEXT,                -- freeform result description
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Runs: individual execution attempts of a task
CREATE TABLE runs (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    status TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running','completed','failed','cancelled')),
    git_ref TEXT,                 -- commit hash at run start
    environment TEXT,             -- JSON: python version, packages, config, pixi lockfile hash
    parameters TEXT,              -- JSON: run-specific params (config variations, seeds, etc.)
    result TEXT,                  -- freeform result / output summary
    metrics TEXT,                 -- JSON: key-value numeric metrics
    worktree_branch TEXT,         -- if run in worktree
    agent_name TEXT,              -- which agent executed this run (lightweight provenance)
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Research notes: unstructured annotations linked to any entity
CREATE TABLE notes (
    id INTEGER PRIMARY KEY,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('investigation','task','run','general')),
    entity_id INTEGER,           -- nullable for general notes
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Schema version for migration
CREATE TABLE schema_version (
    version INTEGER NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Design Notes

**Why `investigation` not `hypothesis`**: Hypotheses are one type of investigation. Using the generic term in the schema avoids overloading "hypothesis" for non-hypothesis work. The CLI could still alias `parallax hypothesis` → `parallax investigation create --type hypothesis` for ergonomics.

**Outcome values differ by type**: `supported/refuted/inconclusive` are scientific outcomes (hypothesis/exploration). `completed/failed/abandoned` are engineering outcomes (feature/custom). Both valid in the same column. The `type` on the parent investigation determines which are semantically appropriate.

**Agent provenance (lightweight)**: `runs.agent_name` tracks which agent executed the run. Not full W3C PROV, but sufficient to answer "who did this?" without a separate provenance system. Can evolve to a full `agent_actions` table in Layer 3 if needed.

**Environment as JSON blob**: Flexible, future-proof. Auto-capture what's available (git ref always, pixi lockfile hash when pixi exists, etc.). Structured enough to query (`json_extract` in SQLite), loose enough to evolve.

**Tags on investigations**: JSON array for informal grouping orthogonal to the parent-child tree. Example: tag `["performance", "redis"]` on multiple investigations across different parent trees.

## External Tool Comparison

| Tool | What it does well | What Parallax does differently |
|---|---|---|
| **MLflow** | Metric logging, run comparison, artifact storage | Parallax adds hypothesis-driven workflow + investigation hierarchy. MLflow is open-loop logging; Parallax is closed-loop (investigate → test → conclude → new investigation). |
| **Sacred** | Automatic env capture, config management | Good idea — Parallax should auto-capture env. But Sacred is ML-focused, no hypothesis lifecycle. |
| **W3C PROV** | Interoperable provenance graphs | Overkill for MVP. Lightweight provenance (agent_name on runs) sufficient. PROV compliance is a Layer 3 goal if needed. |
| **PROV-AGENT** | Agent-specific provenance via MCP | Fascinating but bleeding-edge. The MCP integration could be a future hook. For now, simpler agent tracking. |
| **Neptune** | Comparison dashboards | Comparison is the killer feature. MVP: `parallax task compare I1` (CLI table). Layer 3: visual dashboard. |
| **DVC** | Data versioning | Orthogonal to investigation tracking. Integrate if project has large data. Don't rebuild. |

**Parallax's unique value**: Closed-loop scientific workflow. No existing tool takes you from "I have a question" through "here are the experimental results and whether they support the hypothesis" with persistent state, agent execution, and structured review. MLflow/Sacred/Neptune are all logging-first, not methodology-first.

## Workflow Example (Concrete)

```
1. User: "I think Redis caching will reduce our API query time by 50%"

2. User invokes /hypothesis (or conversation naturally triggers it)
   → Skill guides collaborative formulation
   → Claude + user refine statement, success/failure criteria
   → Skill instructs: `parallax investigation create --type hypothesis \
       --name "redis-query-caching" \
       --statement "Redis caching reduces API query time by >=50%" \
       --success-criteria "p95 latency drops >=50% on benchmark suite" \
       --failure-criteria "latency reduction <20% or regression in write path"`
   → DB: investigation I1 created (proposed)

3. User + Claude design experiments:
   → `parallax task create --investigation 1 \
       --name "benchmark-with-redis" \
       --description "Add Redis cache layer, run benchmark suite" \
       --test-plan "1. Add Redis to docker-compose. 2. Implement cache decorator. 3. Run load test."`
   → `parallax task create --investigation 1 \
       --name "benchmark-without-redis" \
       --description "Control: baseline benchmark without cache"`
   → DB: tasks T1, T2 created (proposed)

4. User approves: "run experiments"
   → User dispatches experiment-runner agent for T1 (Claude Code handles worktree)
   → Agent starts, creates run:
     `parallax run create --task 1 --git-ref $(git rev-parse HEAD)`
   → Agent executes, records result:
     `parallax run update 1 --status completed \
       --result "p95 latency: 45ms → 18ms (60% reduction)" \
       --metrics '{"p95_latency_ms": 18, "p50_latency_ms": 12, "throughput_rps": 450}'`
   → Similarly for T2 (control)

5. User triggers review:
   → result-validator or investigation-reviewer agent reads .parallax/state.md
   → Sees all tasks + runs for I1
   → Synthesizes: "I1 supported. 60% reduction exceeds 50% threshold. Control confirms baseline."
   → `parallax investigation update 1 --status concluded --outcome supported`

6. Report presented to user for final decision.
```

## Remaining Open Questions

These are deferred from the initial design session. To be resolved in future design iterations before implementation begins.

### State Transitions

**Q1**: Can investigations be re-opened? (`concluded` → `active`?) Or must user create a new investigation referencing the old one?

**Q2**: Should `proposed → active` auto-trigger when first task starts? Or require explicit human transition?

**Q3**: What prevents an agent from concluding an investigation without human approval? (Recommendation: CLI `update --outcome` requires `--confirm` flag or is gated in skill instructions.)

### Research Notes

**Q4**: Auto-generated activity log (investigation created, task started, run completed) vs user-authored notes vs both? If both, are they in the same table or separate?

**Q5**: Should notes be queryable by full-text search? (SQLite FTS5 extension supports this cheaply.)

### Environment Capture

**Q6**: Auto-capture scope: minimum (git ref + Python version) vs maximum (full pixi lockfile hash, hardware, OS, seeds)? Trade-off: friction vs reproducibility.

**Q7**: Should `parallax run create` auto-capture environment, or require explicit `--environment` JSON? (Recommendation: auto-capture what's detectable, allow override.)

### Schema Migration

**Q8**: Version-on-open (lightweight, SQLite-friendly) vs Alembic-style migrations? (Recommendation: version-on-open for MVP — check `schema_version` table on DB open, apply any needed ALTER TABLEs.)

### CLI Ergonomics

**Q9**: Should `parallax hypothesis create` be an alias for `parallax investigation create --type hypothesis`? Or should the CLI always use generic terms?

**Q10**: Interactive mode for `create` commands (like `parallax init` interview) vs flag-only? (Recommendation: both — interactive by default, flags for scripting/agent use.)

### Worktree <-> DB Interaction

**Q11**: Worktree agents write to main tree's DB or worktree-local DB? SQLite WAL mode handles concurrent access, but path resolution differs across worktrees.

### Export/Import

**Q12**: Export format: JSON (structured, reimportable) or markdown (human-readable, less precise)? Or both?

**Q13**: Should `/handoff` auto-trigger `parallax export`?

### Concurrency & Resource Limits

**Q14**: How many concurrent experiment runs / worktrees / agents can be spawned at once? Unbounded concurrency risks overwhelming token usage limits (especially pro/5x tiers), machine resources (CPU/memory for worktrees + agent processes), and Claude API rate limits. Options:
- **Token-tier-derived limit**: pro=1 concurrent, 5x=2-3, 20x=4-5, api=unbounded. Tied to existing tier system.
- **User-configurable**: `parallax config set max-concurrent-runs 3`. Explicit, simple.
- **Both**: tier-based default, user override.
- **Queuing**: if more experiments than slots, queue them. `parallax run list` shows queued/running/completed.

Related: should Parallax enforce this limit, or just warn? Claude Code spawns agents via Task tool — Parallax can't easily prevent it. The skill/agent instructions would need to respect the limit ("check `parallax run list --status running` before spawning another agent"). Enforcement via convention (Layer 1 style) vs hard enforcement (Layer 2 hook that blocks agent spawn if over limit)?

## References

- [MLflow Experiment Tracking](https://mlflow.org/classical-ml/experiment-tracking)
- [Sacred + Omniboard](https://github.com/IDSIA/sacred)
- [PROV-AGENT: Unified Provenance for AI Agent Tracking (IEEE e-Science 2025)](https://arxiv.org/abs/2508.02866)
- [W3C PROV Specification](https://www.w3.org/2001/sw/wiki/PROV)
- [Neptune.ai: Best ML Experiment Tracking Tools](https://neptune.ai/blog/best-ml-experiment-tracking-tools)
- [DagsHub: Reproduce Experiments](https://dagshub.com/docs/use_cases/reproduce_experiment_results/)
- [Best ELN Software 2026](https://research.com/software/best-eln-software)
