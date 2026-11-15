# Seam 0: Recorded local evidence

Date: 2026-11-15. Tested code commit:
`46f6f776ce6e92622695ac5f5f977c4b8aa759b7`.
Environment: macOS 27.0.1, ARM64. These are local results, not hosted CI results.

## RED and GREEN

- RED `36b338031ab2`: four table-driven grooming tests produced 13 assertion
  failures/subtests against the callable no-op checker; no missing-symbol/import
  failure was used as RED evidence.
- GREEN `9b652081c418`: all four grooming tests passed without changing expected
  behavior. The orphan-history fixture was corrected to return to its explicit
  original branch rather than relying on Git's previous-checkout shortcut.
- Gate glue initially rejected safe archive entries because macOS's temporary
  `/var` alias was compared to its resolved path. The failed run emitted RESULT
  FAIL. Commit `46f6f776ce6e` resolved both sides and reran successfully.

## Disposable gate runs

Commands were `make gate-seam0 PYTHON=.venv/bin/python` for 3.12 and
`python3.X scripts/gate_seam0.py` for the other installed supported interpreters.
Each run archived the committed source, created and removed its own temporary
environment, restored the existing dependencies and retained evidence.

| Python | UTC run ID | Result |
| --- | --- | --- |
| 3.11.15 | `seam0-20261115T180124Z-323492be` | PASS |
| 3.12.13 | `seam0-20261115T180057Z-42667f4c` | PASS |
| 3.13.15 | `seam0-20261115T180124Z-0cf036f5` | PASS |
| 3.14.6 | `seam0-20261115T180124Z-c2eaed97` | PASS |

Every run passed selected seam freshness, Ruff, all 14 offline unit tests
(10 existing package contracts plus four grooming tests), wheel/sdist build,
Twine checks, source-workflow inclusion and both installed CLI help commands
outside the archived checkout. The default CLI/runtime implementation was not
modified. Dependencies were restored from declared ranges and recorded in
`04-versions.log`; these results do not assert locked dependency reproducibility.

Raw per-step logs and `summary.json` are retained locally under ignored
`.gate-evidence/<run-id>/`. This committed document preserves the durable,
sanitized results without embedding user paths, dependency download logs or
credentials. Keep raw logs private unless separately reviewed for publication.

## Limits

- No emulator, native integration or real AWS call was run for setup.
- Linux/Windows and hosted CI execution were not performed locally. Existing
  CI remains the Linux Python 3.11-3.14 offline matrix; its new history checks
  require a full checkout. Those remote results remain unverified until the
  branch is published and CI runs.
- Native CI, report runtime wiring, tracing, Organizations fixtures, lifecycle
  hardening, capability probes and AWS comparisons are not implemented here.
- The source-distribution gate requires Git history from a checkout for
  freshness; distributing workflow files does not turn an unpacked tarball
  into a Git repository.
