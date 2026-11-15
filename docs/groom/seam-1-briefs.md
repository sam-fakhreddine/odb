Groomed-at: 395ce3b9c9141299686265cfd48beb8c10fc072d
Depends-on: docs/design.md, docs/adr, docs/groom/seam-1-evidence-contract.md, docs/groom/seam-0-briefs.md, aws_emulator_shim, tests/unit
Re-groomed: 2026-11-15; re-groomed at seam-1 start against current main after typed seam 8 landed. Read the implemented `aws_emulator_shim/contracts.py` (StrictContract config, `parse_manifest`/`ManifestError`/`ManifestIssue` safe-diagnostic pattern, hidden-input errors), `aws_emulator_shim/schema.py` (generate/check/drift CLI), `scripts/gate_seam0.py` (disposable gate pattern and per-seam schema/typing steps), `scripts/check_types.py`, `tests/unit/test_typed_contracts.py` and `docs/schemas/manifest-v1.schema.json`. Superseded the standard-library-only proposal with strict Pydantic reuse per ADR 0004 and the feed-forward notes. Chose `docs/schemas/evidence-v1.schema.json` (co-located with the manifest schema) over the brief's provisional `docs/evidence-v1.schema.json`; this interface choice is recorded as a behavior decision in the as-built note. Reuse seam-8 gates: add the evidence module to strict mypy and add an evidence schema-drift step to the disposable gate. Four acceptance tests remain the budget.
Re-groomed: 2026-11-15; closure. Read the RED (`9d0be61`) and GREEN (`a5d5d0c`) contracts and the gate changes (`7dad330`), then the as-built docs (`395ce3b`). Set Groomed-at to the last dependency-touching commit so the seam-1 disposable gate checks only its own freshness against HEAD.

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
