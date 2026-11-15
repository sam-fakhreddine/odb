# ODB handoff

Date: 2026-11-15. Active branch: `feature/auto-semver`.

## Current work

Seam 10 adds opt-in release-please version proposals, without automated tags
or releases. See [seam 10 evidence](groom/seam-10-evidence.md) and
`CONTRIBUTING.md` for prerequisites and the manual pending-label handoff.
It is a separate local branch; no GitHub workflow has been run. Read
`AGENTS.md`, the design/ADRs and `docs/groom/index.md`. Seam 1 is intentionally
stale on this branch. Other runtime feature branches remain separate.

## Resume

Run `make groom-check` after committing and `make groom-check SEAM=N` before
starting the chosen seam. Read dependency history and actual code, re-groom
only that seam, commit and recheck. No real-AWS execution, push, PR or release
is authorized by this handoff. Pending owner tasks are in `docs/human-tasks.md`.

## Evidence

See [setup evidence](groom/seam-0-evidence.md). The setup gate passed for
commit `46f6f776ce6e92622695ac5f5f977c4b8aa759b7` on macOS ARM64,
Python 3.11.15, 3.12.13, 3.13.15 and 3.14.6. Each run passed 14 offline tests,
lint, builds, distribution and installed-wheel CLI checks. Linux/Windows,
hosted CI and native/AWS behavior were not verified by setup.

Seam 10's disposable gate passed at
`0c3183877ca60f8394e70c9d1589ab4c8350b04b`. Closure documentation follows
that tested revision. Raw logs remain private in ignored `.gate-evidence/`;
the committed summaries are the portable records.
