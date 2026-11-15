Groomed-at: d24ca892cd1be89501bc9d687b87b04c9617d8a5
Depends-on: docs/design.md, docs/adr, docs/groom/seam-1-evidence-contract.md, docs/groom/seam-0-briefs.md, aws_emulator_shim, tests/unit

# Seam 1 worker briefs

## 1.0 Re-groom first

Run the freshness gate before implementation. Read actual setup commits and
current runtime/CLI/receipt types. This ahead-groomed plan is expected to be
stale after setup. Update it only when seam 1 starts, commit and check again.

## 1.1 RED

Create callable, no-op record/aggregate/serialize entry points in
`aws_emulator_shim/evidence.py`; choose signatures after source inspection.
Add `tests/unit/test_evidence.py` with four literal tables corresponding exactly
to the four Done-when outcomes. Each test has `Catches:`; privacy tests name the
non-disclosure property. Fail on assertions, not missing symbols. Commit RED.

Rows: native passed, adapted passed, failed and not-tested checks; unknown and
not-checked AWS status; duplicate/missing required IDs; expected negative
control; attempted/unconfirmed write; rejected credential/payload fields.
Use synthetic operation names/metadata, never actual credentials.

## 1.2 GREEN

Implement a small standard-library evidence contract: schema version, run ID,
stable check IDs, outcome, provenance, coverage, optional fault/fixture IDs and
AWS-validation state. AWS state is independent and cannot be inferred from local
success. Use explicit unknown/not-checked values when observations are absent.

Keep assertion outcome distinct from operation outcome. A report's integrity
hash is not proof of execution. Do not treat not-tested checks as passing or
implement permission/network parity. Prefer immutable values and typed fields.
Reject unexpected fields rather than guessing redaction. Preserve existing
package APIs and CLI output; adding the module alone enables no feature.

## 1.3 Gate and feed forward

Publish `docs/evidence-v1.schema.json` with one synthetic example and a contract
validation command, using an existing validator if available or documenting a
small validation dependency deliberately. JSON parsing alone is not schema
validation. Implement `scripts/gate-seam1.sh` using the setup pattern and record
evidence. Four tests are the budget; justify additions in the spec.

Feed field names/check IDs and unknown/provenance semantics into tracing,
Organizations, capability and CI outlines. Do not groom those future seams.
Next evidence slices separately add CLI opt-in, atomic partial reports and
runtime provenance; no real AWS calls belong here.

## Feed-forward decision: 2026-11-15

Setup now provides `scripts/groom_check.py`, `make groom-check SEAM=N` and
`scripts/gate_seam0.py` as the disposable gate pattern. Reuse its resolved
temporary-root handling, actual interpreter/dependency recording and explicit
non-native scope. Global CI reports stale future briefs; the active seam gate
enforces only its own freshness. Full Git history is required.

This note intentionally does not advance Groomed-at. Read the actual committed
tooling before implementing seam 1. Its future gate must not invoke the setup
gate's hard-coded `--seam 0` as its own freshness criterion.

## Feed-forward decision: 2026-11-15, schema first

Owner: "while we are early can we do a strongly typed and ZOD style first".
ADR 0004 inserts typed-contract seam 8 before this seam. Supersede 1.2's
standard-library-only model proposal with strict Pydantic contracts and extend
the new mypy/schema gates when evidence starts. Reuse shared model configuration
and safe error conventions rather than independently choosing another validator.
Do not treat generated structural JSON Schema as cross-record semantic proof.
This is feed-forward only; Groomed-at stays unchanged until seam 1 starts.
