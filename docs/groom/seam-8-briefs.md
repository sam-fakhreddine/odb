Groomed-at: cddacfd38c358245ee6f3b1de8332875869ec41d
Depends-on: docs/design.md, docs/adr, docs/groom/seam-8-typed-contracts.md, aws_emulator_shim, pyproject.toml, scripts/gate_seam0.py, scripts/check_types.py, tests/unit, tests/typing, docs/schemas/manifest-v1.schema.json, .github/workflows/ci.yml, Makefile
Re-groomed: 2026-11-15; inspected current main, inventory validation, CLI, release workflow and existing local implementation before starting issue 7.
Re-groomed: 2026-11-15; account for the assertion-only RED commit and unchanged acceptance tables.
Re-groomed: 2026-11-15; reviewed GREEN contracts and the current gate; preserve seam 10 while adding seam 8 schema and isolated-wheel typing.
Re-groomed: 2026-11-15; reviewed recovered implementation and four passing interpreter gates; close locally against current main.
Re-groomed: 2026-11-15; reproduced merged PR 17's unmatched account/role key schema bypass; extend the existing structural acceptance table, then close mappings through model metadata and regenerate schema.
Re-groomed: 2026-11-15; inspected the assertion-only RED mapping table (12 failures); implement additionalProperties through field metadata without changing accepted Python inputs.
Re-groomed: 2026-11-15; reviewed GREEN metadata and regenerated schema; use the full commit hash required by the freshness gate.

# Seam 8 worker briefs

## 8.0 First seam after setup

Run the committed freshness check for seam 8. The next evidence brief stays
stale until selected. Do not infer native/AWS behavior from contract validation.

## 8.1 RED

Add callable `parse_manifest`/`load_manifest` stubs and a public `ManifestError`
in `aws_emulator_shim/contracts.py`. Return an inert value from parse, raise the
explicit contract error from the loader. Do not fail on missing imports.
Use four tests corresponding to the spec, with `Catches:` docstrings:
roundtrip/schema, invalid shapes/relationships, immutable/private JSON parsing,
and opt-in Harness/CLI boundary behavior before startup. Commit actual RED.

## 8.2 GREEN

Implement `Account`, `Route` and `Manifest` strict Pydantic models. Annotated
field constraints drive generated schema; model validators cover cross-record
relationships. Use read-only mappings plus serializers, not just shallow
`frozen=True`. Pydantic trusted construction/copy escape hatches are not
untrusted-data parsers. Re-validate typed inputs at the public parser boundary.

Use structured allowlisted path/code errors, excluding raw input and context.
Unknown dynamic keys are represented by `*` in diagnostics. Keep file I/O
errors explicit. The JSON file loader rejects duplicate keys/non-finite values.
No silent coercions, ignored extra fields or success-shaped invalid results.

Add independent `strict_manifest=False` to Harness, and `--strict-manifest`
to the existing CLI. Normalize validated data only when selected. Share one
contract API with the loader/CLI; do not rewrite runtime SDK calls.

## 8.3 Glue

Declare Pydantic 2 and mypy/jsonschema before restoring dependencies. Strict
mypy covers new contract/schema code and a positive consumer; a separate
negative consumer has exactly four errors (two wrong argument types, one
unknown constructor field, one unknown model attribute). Add `py.typed`.
Generate `docs/schemas/manifest-v1.schema.json` from code, with a check command.
CI/gate runs both positive and negative checks and structural schema tests.

## 8.4 Gate and feed forward

Gate clean committed HEAD with recorded environment. Verify marker and new API
from the installed wheel outside source; consumer imports must not degrade to
Any or be satisfied accidentally by checkout files. Record exact scope/limits,
test outcomes and as-built differences. Feed the chosen model/toolchain into
evidence briefs without advancing their Groomed-at baseline.

## Closure

Locally closed against `59768b8873bb748d19ec61c39a830308f53099c9`.
See `seam-8-evidence.md`. Strict typing covers new contracts and their
consumers, not the entire legacy runtime or AWS behavior.

## Mapping-key follow-up

Layer: structural contract boundary. Test budget: extend the existing schema
test method with account/role mapping rows, no new test methods. Record
assertion-failing RED and GREEN separately. Reject unmatched names with both
valid and invalid values, retain valid names and value validation, and check
both direct model generation and the checked-in schema. Keep legacy behavior
and semantic validation unchanged. Run the seam-8 disposable gate.
