# ODB handoff

Date: 2026-11-15. Active branch: `feature/seam-workflow`.

## Current work

Seam 0 is being established. Runtime features 1-7 are not implemented by setup.
Read `AGENTS.md`, the design/ADRs and `docs/groom/index.md`.
Seam 1 is groomed ahead; future features are outline rows only.

## Resume

Run `make groom-check` after committing and `make groom-check SEAM=N` before
starting the chosen seam. Read dependency history and actual code, re-groom
only that seam, commit and recheck. No real-AWS execution, push, PR or release
is authorized by this handoff. Pending owner tasks are in `docs/human-tasks.md`.

## Evidence

Setup gate not yet run. Update this section at closure with the tested SHA,
environment and sanitized durable evidence reference.
