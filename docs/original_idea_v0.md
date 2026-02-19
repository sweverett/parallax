# Original Parallax Idea Document

> Archived verbatim from `parallax_idea.md` on 2026-02-19 during project bootstrap.
> This is the unmodified original vision document. See `VISION.md` for the structured version.

---

Parallax: Two perspectives (human / AI) to get a stronger result

This is intended to be some sort of software tool and / or app and / or desktop interface that is both mission control for streamlining your personal scientific work as well as automating / encoding scientific best practices into standard but industry leading agentic AI coding practices leveraged specifically for maximally effective, efficient, and reproducible science. Personal science use case for now, don't need significant team / mission / enterprise support yet.

Principles:

1. AI tooling (particular agentic coding & agents) *supplement* scientific work, not drive it
    1. Start with Claude for MVP, could always expand later (particularly for a good free model)
2. Automates lots of "best practices" for agentic coding
    1. Asks explicitly up-front for each new project (dir) what the purpose is, what the core foundations/pillars are, what to do, what never/not to do, main database / repos & access, main libraries to use, main papers or documents to reference, main regression tests to start with, style guidelines, etc.
        1. This is to streamline making a [CLAUDE.md](http://CLAUDE.md) file that is hyper effective for scientific work
    2. Augment the user-specified [CLAUDE.md](http://CLAUDE.md) file with [PARALLAX.md](http://PARALLAX.md) file (or just section at the end of CLAUDE.md) with parallax-specific commands related to:
        1. Asking the user for hypotheses for each task before generating N of them itself, and for the user to prioritize the ranking of them
        2. Extreme version control, automation of semantic versioning & package publishing, etc.
        3. Orchestration elements (agent teams, skills, etc.), English to coding interface, etc.
            1. Also voice option
        4. An efficient summary markdown system at all code repo dirs, test dirs, experiment dirs, hypothesis dirs, test result dirs, etc. so we can track all of this with minimal context rot
        5. Some system that (a) knows of context rot and adjusts when we pass off research & plan findings and/or implementation status and test result status to the next agent efficiently and (b) relative prioritization of each implementation and/or hypothesis task so that the user is using their available token budget effectively over time without going over limits or costing extra usage (though allow user to add money for it, off by default)
        6. Very explicit & reproducible environment setup for all projects so each task with associated hypotheses can be tagged with a specific version & commit, with a lot of this automated when reasonable (such as incremental semantic versioning tags)
            1. Open to different solutions here, but perhaps back-end containers that would also work at most HPCs are a good solution? But not have the user have to realize or bother with the setup? Lighter weight solutions could also be ok, but need to be reproducible across different systems & architectures
        7. Good CI / unit test/ interface test / regression test practices with GitHub integration
        8. All agents ending a task need to output a summary of their problem, findings, implementations, and quantitative results in an organized way to pass off to future agents and tasks
        9. Very explicit *strong* preferences for good scientific practice, such as library (packages, scripts, etc.) over notebooks, version control & history, reproducibility, accuracy & precision over feature/merge velocity, highest quality work, etc.
            1. Point is to accelerate *excellent & reproducible science, NOT* faster junk papers. We are trying to speedup robust science but no faster than that
            2. Be explicit that:
                1. *NEVER* reduce test tolerance thresholds, scope, or simple passes just to make the test pass after a failure without *EXPLICIT HUMAN APPRO*V*AL*
        10. Perhaps some output format of a project can be exported in the future for easy reproduction of results
        11. Basic rules for code formatting, type hints / mypy (if python), etc. if not conflicting with user [CLAUDE.md](http://CLAUDE.md) file
        12. ... (more?)
3. Keeps text logs of all conversations saved by date and subcategories, along with summaries for each day to act as a scientific log (with exact conversation copies in low-cost txt files for further examination). Section for plots produced as well
4. Dashboard for all projects
    1. Dashboard for each project
        1. Conversation logs & summaries by date
        2. Ongoing tasks,
            1. Each has a section for all ongoing & previously tested hypotheses
                1. Each hypothesis has a summary, prioritization, unit/interface/regression/bespoke test results, diagnostic plots, etc., and a quantitative conclusion
                2. When all hypotheses have completed, qualitative & quantitative summary of all findings, plan for proceeding, and always ask for human input on next steps
            2. Each set of hypothesis for a given task that have tests run must have a clear version/commit/etc.
            3. A Jupyter Lab hub for human experiments or AI-produced notebooks/tutorials/experiments for the humans to play with, after the basic infrastructure is setup
                1. Each project env (and any additional envs should automatically be setup to work with this env
        3. Linking of most important information from GitHub, such as repo page, issues, PRs, CI status, branch/commit diagram of history, etc.
            1. Maybe have some tools which recommend & automate (if requested) various merge approaches such as merges, rebases, squash merges, etc. for those who don't understand them well (can always give a recommendation given git history)
    2. For fun: Each startup shows an abstract or fun visual of an impactful but lesser-known scientist along with a very brief (2-4 sentence) summary of their impact and personal life. Summarized from a trustworthy source (maybe wikipedia?)
5. Daily (or by request) audits of the project code for:
    1. Unidentified bugs
    2. Possible concerns (not necessarily a current bug, but related to where the project is going)
    3. Good feature additions given the project scope
    4. Recommendations for further tests to add
    5. Other?
6. Daily (or by request) tracking of all regression tests with visual time series metrics of changes over time, as function of date/commit/version/etc.
    1. Lots of this can be configurable by user

Questions to answer:

1. ...

Other:

1. ...
