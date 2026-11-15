# ADR 0003: Standard-library grooming and offline disposable gates

Date: 2026-11-15. Status: accepted for the setup seam.

## Context

ODB supports Python 3.11-3.14 and already uses unittest, Ruff, build and Twine.
The setup must not require an emulator, AWS account or a new Python dependency.

## Decision

Implement grooming checks using Python's standard library and Git, with
`make groom-check [SEAM=N]` as a convenience. Direct script invocation remains
available. Use synthetic temporary Git repositories for history-sensitive tests.

The setup gate archives a clean committed revision to a private temporary
directory, creates a fresh virtual environment, installs missing existing
development requirements, and runs freshness, lint, offline tests, distribution
checks and installed-wheel CLI help outside the source tree. No emulator or
AWS call belongs to this setup gate.

Print PASS/FAIL per step and one RESULT line; preserve logs and summary metadata
outside the disposable workspace. Cleanup removes only the directory allocated
by the gate. Evidence identifies the tested commit, interpreter/platform and
dependency versions. It is not a reproducible lockfile or native integration
result. Gate evidence is ignored locally; retain sanitized evidence externally
when handing off.

## Consequences

The gate needs Git, Python with venv/pip, and access to already declared Python
dependencies (or a configured trusted cache). Missing prerequisites fail
explicitly. Run each supported interpreter in CI; platforms not run locally
remain unverified. Network package installation is not an AWS runtime call.
Do not silently expand the platform matrix or add expensive native integration
to ordinary offline CI.

## 2026-11-15: Typed foundation amendment

The standard-library constraint above applies to the setup checker, not every
future runtime feature. ADR 0004 introduces Pydantic and static/schema checking
for the typed-contract seam. Reuse this disposable gate with the active seam's
freshness selector and additional typed-contract checks; do not permanently
gate closed seam 0 when evaluating a later seam.
