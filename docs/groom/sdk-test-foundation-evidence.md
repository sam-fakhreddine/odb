# SDK typing and property-test foundations: evidence

Date: 2026-11-16. Tested commit: `cf8deb23d64934ae6717bac7ec4f5936aa1a6679`.
Environment: macOS ARM64, host Python 3.15.1. Local results only: not hosted CI,
not a native emulator, and not real AWS verification. This closes issue
`sam-fakhreddine/odb#9`.

## Scope

Developer-only: added boto3 S3/SQS/STS stubs and Hypothesis as `[dev]` extras,
annotated `local_session` parameters and its `boto3.Session` return, and added
SDK typing consumers plus four deterministic property tests. No runtime behavior
or production dependency changed: `dependencies` remains
`["boto3>=1.40.66,<2", "pydantic>=2.12,<3"]`.

## Resolved dependency versions

boto3 1.44.4, boto3-stubs 1.44.3, botocore-stubs 1.43.126, hypothesis 6.170.15,
pydantic 2.14.3, mypy 1.20.2 (from a fresh isolated venv install of `.[dev]`).

## Checks (clean disposable venv, HEAD only)

- Offline unit suite: 26 tests pass, including the four new Hypothesis property
  tests (out-of-range/non-int port rejection, rejected-value non-disclosure,
  immutable round-trips immune to source mutation, bridge-to-self/undeclared
  rejection). Run twice with identical results.
- `scripts/check_types.py` (source): strict positive SDK and contract consumers
  pass; the existing four contract typing errors and three new SDK errors
  (`call-arg`, two `arg-type`) are rejected as expected.
- Structural schema drift checks (manifest and evidence) pass.
- `python -m build` and `twine check` pass; the wheel ships `py.typed` plus
  `runtime.py`, `contracts.py`, `evidence.py` and `schema.py`.
- Installed wheel: both CLI entry points print help, and
  `check_types.py --installed` re-runs the positive SDK/contract consumers and
  both negative fixtures against the isolated wheel with the expected errors.

## Note on the gate

Issue #9 has no committed `docs/groom/seam-N-briefs.md`, so there is no
dedicated `make gate-seamN` for it; the existing per-seam gates also assert their
own brief freshness, which this shared-code change legitimately makes stale for
seam 1. In place of that I ran the same clean-room steps the disposable gate
runs (lint, offline suite, schema drift, source and installed-wheel static
contracts, build, distribution metadata, wheel contents, CLI help) and captured
`verify.log` in the ignored evidence directory. The raw log stays in
`.gate-evidence/sdk-foundation-20261116T172931Z/`; this summary is the portable
record.

## Limitations

The host interpreter (3.15.1) is outside the declared 3.11-3.14 support matrix and
does not re-verify it; hosted CI runs the 3.11-3.14 matrix separately. Property
tests are deterministic by `derandomize=True` and a disabled example database, but
are not a proof of AWS or emulator behavior. No emulator or AWS call was made.
