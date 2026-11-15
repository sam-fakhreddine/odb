# ODB handoff

Date: 2026-11-15. Active branch: `feature/seam-workflow`.

## Current work

Seam 0 is locally closed. Runtime features 1-7 are not implemented by setup.
Read `AGENTS.md`, the design/ADRs and `docs/groom/index.md`.
Seam 1 is groomed ahead and intentionally stale; future features are outline
rows only. The existing all-zero native identity and adapter boundaries are
unchanged. All commits remain on the local setup branch, not published.

## Resume

Run `make groom-check` after committing and `make groom-check SEAM=N` before
starting the chosen seam. Read dependency history and actual code, re-groom
only that seam, commit and recheck. No real-AWS execution, push, PR or release
is authorized by this handoff. Pending owner tasks are in `docs/human-tasks.md`.

## Evidence

See [setup evidence](groom/seam-0-evidence.md). The disposable gate passed for
commit `46f6f776ce6e92622695ac5f5f977c4b8aa759b7` on macOS ARM64,
Python 3.11.15, 3.12.13, 3.13.15 and 3.14.6. Each run passed 14 offline tests,
lint, builds, distribution and installed-wheel CLI checks. Linux/Windows,
hosted CI and native/AWS behavior were not verified by setup.

Grooming/closure documentation commits follow the tested code revision. Run the
gate against current committed HEAD when resuming. Raw logs remain private in
ignored `.gate-evidence/`; the committed summary is the portable record.
