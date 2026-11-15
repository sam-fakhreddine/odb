Groomed-at: 61ddc752c315007486140fb5d505971377e6f9f9
Depends-on: docs/design.md, docs/adr, docs/groom/seam-8-typed-contracts.md, aws_emulator_shim, pyproject.toml, scripts/gate_seam0.py, tests/unit
Re-groomed: 2026-11-15; inspected current main, inventory validation, CLI, release workflow and existing local implementation before starting issue 7.

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
