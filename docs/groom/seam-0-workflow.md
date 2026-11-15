# Seam 0: Workflow setup

Status: locally closed 2026-11-15; owner: "ok do the setup".
Branch: `feature/seam-workflow`. Starts from the existing package baseline.

## Why

Development needs a committed, executable way to notice stale plans and retain
evidence. Set up that machinery without implementing any proposed runtime feature.

## Done when

- Committed briefs with missing/malformed headers or invalid dependency/base
  metadata fail explicitly in both modes. Acceptance: header/base fixture table.
- A substantive dependency change warns in report mode and blocks its seam
  in gate mode; unrelated changes do neither. Acceptance: dependency fixture table.
- Own re-groom commits and upstream bookkeeping-only edits do not cascade;
  substantive upstream edits still block. Acceptance: bookkeeping fixture table.
- Real merge/history cases and literal directory dependencies remain visible,
  including removals and unavailable shallow history. Acceptance: history fixture table.
- A clean committed setup revision passes a disposable offline gate, with
  per-step verdicts and retained environment/commit evidence. Acceptance: gate run.

## Turns

| Turn | What | Layer | Test / budget |
| --- | --- | --- | --- |
| 0.1 | Commit design, ADRs, specs and briefs | Docs | Review local links/quoted decisions |
| 0.2 | RED callable checker stub and literal history fixtures | Core/tooling | Four table-driven test methods; assertion failures |
| 0.3 | GREEN committed-history checker | Core/tooling | Same four tests, no relaxed expectations |
| 0.4 | Add Make targets, gate, CI freshness enforcement and contributor guidance | Glue/config | Lint and recorded disposable run |
| 0.5 | Re-groom setup, run gate and record as built/handoff | Docs/gate | `make groom-check SEAM=0`, `make gate-seam0` |

Four test methods cover focused rows rather than a separate test for every
Git command. Budget excludes the pre-existing package unit tests. Additional
cases require a reason here before implementation.

## Gate

1. Refuse dirty/untracked nonignored files; identify the tested commit.
2. Archive that revision into a disposable directory and create a fresh venv.
3. Gate committed seam-0 freshness; report future stale plans without blocking.
4. Run Ruff and all offline unit tests (including grooming fixtures).
5. Build wheel/sdist, check metadata and source-workflow inclusion.
6. Install the wheel separately and invoke both CLI help commands outside source.
7. Print RESULT and preserve per-step logs plus environment/dependency metadata.

No emulator, Docker/Podman or AWS prerequisite is part of this gate. Other
platform/interpreter verification is recorded separately, never implied.

## Progress record

| Date | Turn | Commit | Result |
| --- | --- | --- | --- |
| 2026-11-15 | 0.1 | See Git history for this file | Initial grooming |
| 2026-11-15 | 0.2 | `36b338031ab2` | RED: four methods, 13 assertion failures/subtests |
| 2026-11-15 | 0.3 | `9b652081c418` | GREEN: same expected behavior; fixture branch-return repair |
| 2026-11-15 | 0.4 | `4062371f5771` | Gate/Make/CI and packaging glue |
| 2026-11-15 | 0.5 | `46f6f776ce6e` | Gate PASS, macOS ARM64, Python 3.11-3.14; [evidence](seam-0-evidence.md) |

## As built

Bootstrap exception and bookkeeping grammar are in ADR 0001. CI uses report
mode rather than permanently gating seam 0: a closed seam must not block later
features after a new ADR. Each active seam's own gate enforces its freshness.

The checker rejects shallow repositories explicitly rather than attempting an
incomplete history verdict. Both Make and direct Python commands are supported.
The gate uses an archived source snapshot and fresh venv, not an emulator;
dependency downloads can occur. Raw evidence stays ignored; durable sanitized
results are committed separately. A temporary-directory alias issue was fixed
within the seam. No test expectations were loosened. Other operating systems
and hosted CI remain unverified, not represented as native/integration proof.
