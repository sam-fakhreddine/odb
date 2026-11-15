# ODB handoff

Date: 2026-11-15. Active branch: `feature/typed-contracts-main`.

## Current work

Seam 8 is locally closed on this branch for issue `sam-fakhreddine/odb#7`.
ADR 0004 retains Python and chooses Pydantic with strict static checks.
`strict_manifest=True` and `--strict-manifest` are opt-in; legacy defaults
remain unchanged. Seam 1 remains stale until selected.

Seam 10's proposal workflow is merged and has created a 0.2.0 proposal.
Tags and releases remain manual; see `CONTRIBUTING.md` for the pending-label
handoff. Read `AGENTS.md`, the design/ADRs and `docs/groom/index.md`.

## Resume

Run `make groom-check` after committing and `make groom-check SEAM=N` before
starting the chosen seam. Read dependency history and actual code, re-groom
only that seam, commit and recheck. No real-AWS execution, push, PR or release
is authorized by this handoff. Pending owner tasks are in `docs/human-tasks.md`.

## Evidence

See [typed-contract evidence](groom/seam-8-evidence.md): the clean disposable
gate passed on macOS ARM64, Python 3.11-3.14 at
`59768b8873bb748d19ec61c39a830308f53099c9`. Hosted CI and real AWS were not run.

See [setup evidence](groom/seam-0-evidence.md). The setup gate passed for
commit `46f6f776ce6e92622695ac5f5f977c4b8aa759b7` on macOS ARM64,
Python 3.11.15, 3.12.13, 3.13.15 and 3.14.6. Each run passed 14 offline tests,
lint, builds, distribution and installed-wheel CLI checks. Linux/Windows,
hosted CI and native/AWS behavior were not verified by setup.

Seam 10's disposable gate passed at
`0c3183877ca60f8394e70c9d1589ab4c8350b04b`. Closure documentation follows
that tested revision. Raw logs remain private in ignored `.gate-evidence/`;
the committed summaries are the portable records.
