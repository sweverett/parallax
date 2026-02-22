# Plan 002: cmux + Parallax Integration

## Context

Research comparing Parallax and [cmux](https://github.com/manaflow-ai/cmux) found zero scope overlap but strong complementarity. Parallax defines scientific methodology and workflow; cmux provides terminal infrastructure for parallel agent sessions. This document captures the integration design.

## What is cmux?

cmux is a native macOS terminal multiplexer built on libghostty. Key features:
- **Native macOS app** — not a terminal emulator wrapper; uses libghostty rendering
- **Vertical tabs / workspaces** — organize parallel sessions visually
- **Notification rings** — per-pane completion/alert notifications
- **Socket API** — programmatic workspace/pane creation and management
- **CLI interface** — `cmux notify`, `cmux workspace`, etc.
- **OSC sequences** — standard terminal escape sequences for notifications

## Scope Comparison

| Concern | Parallax | cmux |
|---------|----------|------|
| Domain | Scientific methodology | Terminal infrastructure |
| What it decides | *What* to run, *why*, *when* to stop | *Where* to run it, *how* to display |
| Core primitive | Hypothesis lifecycle | Pane/workspace/session |
| State tracking | SQLite (hypotheses, results) | Terminal session state |
| Agent coordination | Workflow rules, handoff protocols | Process placement, visual layout |
| Enforcement | Hooks, CI, constitution | n/a (infrastructure) |
| Platform | Cross-platform (Python) | macOS only (libghostty) |

Zero overlap. Parallax is the brain; cmux is the nervous system.

## Integration by Parallax Layer

### Layer 1 (Convention System) — available now

Minimal, hook-based integration:

- **Hook notifications via cmux CLI.** `stop_check` and `test_guard` hooks can invoke `cmux notify` to surface alerts as native macOS notifications instead of inline terminal output. Useful when running long experiments in background panes.
- **Implementation:** Add optional `cmux notify` calls to hook scripts. Detect cmux availability; no-op if absent.
- **Effort:** Small. Additive to existing hooks, no architectural changes.

### Layer 2 (State + Workflow Engine)

Git worktree sessions mapped to cmux infrastructure:

- **Hypothesis branches as parallel panes.** When Parallax creates git worktrees for parallel hypothesis exploration, each worktree maps to a cmux pane or workspace. Visual separation matches logical separation.
- **Workspace-per-experiment.** `parallax experiment` creates a cmux workspace with pre-configured panes: agent session, test runner, log tail.
- **Handoff visualization.** Agent handoff summaries could trigger cmux workspace switches, visually moving focus to the next agent's context.
- **Implementation:** cmux socket API for workspace/pane creation. Parallax workflow engine calls socket API when spawning worktree sessions.
- **Effort:** Medium. Requires socket API client, workspace layout templates.

### Layer 3 (Full Orchestrator)

cmux as orchestration substrate:

- **Parallax decides what; cmux handles where.** The orchestrator determines which hypotheses to explore in parallel, allocates token budgets, manages agent lifecycles. cmux provides the physical terminal infrastructure — pane creation, process placement, output routing.
- **Socket API as control plane.** Parallax orchestrator communicates with cmux via socket API to:
  - Create/destroy workspaces for experiment batches
  - Route agent output to designated panes
  - Aggregate notifications (experiment complete, test failure, budget exhausted)
  - Query session state (which panes are active, which agents are running)
- **Dashboard integration.** cmux's visual layout could serve as a lightweight dashboard alternative before building a full TUI/web dashboard. Pane titles, notification rings, and workspace organization provide experiment status at a glance.
- **Effort:** Large. Full socket API integration, layout management, state synchronization.

## Concrete Integration Points

### Socket API
- Workspace CRUD (create experiment workspaces, tear down completed ones)
- Pane management (spawn agent sessions, attach log viewers)
- Session queries (active panes, running processes)

### OSC Sequences
- Pane title updates (hypothesis name, experiment status)
- Notification triggers (test pass/fail, experiment complete)
- Progress indicators

### CLI Hooks
- `cmux notify` from Parallax hooks (test_guard, stop_check, lint_check)
- `cmux workspace create` from worktree creation
- Conditional on cmux availability — graceful no-op otherwise

## Synergistic Workflows

### Parallel Hypothesis Exploration
1. User invokes `/hypothesis` with N candidates
2. Parallax creates N git worktrees (Layer 2)
3. cmux creates N panes, one per worktree
4. Agents run in parallel, each in their own pane
5. Notifications fire as hypotheses conclude
6. Results compared in a summary pane

### Experiment Monitoring
1. `parallax experiment` creates cmux workspace
2. Panes: agent session | test runner | metrics log
3. Hook notifications surface as cmux alerts
4. Stop check fires when experiment concludes — workspace highlights

### Agent Handoff
1. Agent A finishes, writes handoff summary
2. Parallax triggers cmux workspace switch to Agent B's pane
3. Agent B starts with handoff context loaded
4. Visual focus follows logical workflow

## Platform Considerations

cmux is macOS-only (libghostty dependency). Parallax must remain cross-platform.

- **cmux integration must be optional.** All Parallax features work without cmux; cmux adds visual/infrastructure enhancement.
- **tmux fallback.** Linux/HPC users need equivalent functionality via tmux. Same Parallax workflow engine, different terminal backend. Abstract the multiplexer interface: `cmux` on macOS, `tmux` on Linux.
- **Abstraction layer.** Define a `TerminalMultiplexer` protocol (Python Protocol class) with implementations for cmux and tmux. Parallax workflow engine codes against the protocol, not the backend.
- **Detection.** Runtime detection: check for `cmux` binary first, fall back to `tmux`, fall back to no-op (single terminal, no pane management).

## Open Questions

- cmux socket API stability — is the API versioned? Breaking changes would affect Parallax integration.
- tmux feature parity — can tmux replicate cmux's notification rings and workspace model?
- Performance overhead — does socket API communication add meaningful latency to experiment startup?
- Multi-monitor — how does cmux handle workspace-per-monitor? Relevant for dashboard-style layouts.
- Remote sessions — SSH + cmux? HPC users often work on remote clusters.
