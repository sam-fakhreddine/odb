# ODB seam index

Owner, 2026-11-15: "ok do the setup". Workflow: `AGENTS.md` and ADR 0001.
Only seams 0, 1 and 10 are fully groomed. Features 2-7 are deliberately outlines;
split them into thin seams when selected, not seven monolithic changes.

| Seam / feature | Spec | What | Depends on | Gate / control |
| --- | --- | --- | --- | --- |
| 0, locally closed | [Setup](seam-0-workflow.md) | Development contracts, freshness check, disposable baseline gate | Existing package | `make gate-seam0`; [local evidence](seam-0-evidence.md) |
| 1 | [Evidence contract](seam-1-evidence-contract.md) | Offline validated evidence record; no CLI behavior change yet | 0 | Planned `make gate-seam1`; evidence feature branch |
| 2 | Outline | Observed call tracing and sequence export with fixture/AWS-check labels | Evidence IDs/contract | Planned opt-in tracing; own feature branch |
| 3 | Outline | Collision-safe lifecycle and owned-resource recovery | Existing runtime; evidence integration | Planned opt-in managed lifecycle; own feature branch |
| 4 | Outline | Validated local Organizations snapshot and explicit read fixture | Account binding contract | Planned off/fixture mode; own feature branch |
| 5 | Outline | Adapter-free native capability probes with falsification | Probe contracts; evidence integration | Planned explicit probe command; own feature branch |
| 6 | Outline | Pinned native integration CI | Package acquisition; scenario/probe contracts | Planned manual workflow; own feature branch |
| 7 | Outline | Bounded real-AWS scenario comparison | Scenario/evidence contracts; separate authorization | Planned separate command; own feature branch |
| 10, locally closed | [Automatic version proposals](seam-10-autosemver.md) | Opt-in semantic version PRs, no automatic releases | Existing release and workflow setup | [Local evidence](seam-10-evidence.md); `feature/auto-semver` |

Preferred integration order is the table order, not an assertion that all
previous rows are prerequisites. Lifecycle, Organizations validation and CI
acquisition can proceed independently once interfaces are agreed. Parallel
native matrices require collision-safe lifecycle or serialized execution.

## Working rules

Run `make groom-check` after committing to report stale future briefs. Start
only the selected seam with `make groom-check SEAM=N`. Re-groom just in time,
read real code and dependency commits, and record feed-forward findings without
advancing future baselines. Every turn has a test and budget; going over needs
a written reason. Record results with evidence; do not close a red local gate.

Owner, 2026-11-14: "each is a feature branch / flag". Proposed branch names:
`feature/run-evidence`, `feature/call-tracing`, `feature/runtime-reliability`,
`feature/org-state-import`, `feature/native-capability-tracking`,
`feature/pinned-native-ci`, `feature/aws-scenario-comparison`.
Runtime controls default off; CI uses explicit workflow controls.

## Enhancements and ideas

- Owner, 2026-11-14: "we also need a way to send in ORG state to emulate an organizations".
  Selected as feature 4; first implementation is a logical fixture proposal,
  not permission to claim native Organizations state or enforce SCPs.
- Owner, 2026-11-15: "i think i would also like a trace of what calls were made?"
  and "and it shows where it had to be faked and to check actual aws".
  Selected as feature 2. Diagram generation must distinguish unknown internals
  and concurrent observations from inferred causality.
- No additional ideas are selected by this setup.
