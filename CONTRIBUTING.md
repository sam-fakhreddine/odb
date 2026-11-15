# Contributing

ODB is early-development MIT-licensed software. Keep changes small, document
native versus simulated behavior, and never turn an emulator gap into a fake
successful integration.

## Seam development

Read [AGENTS.md](AGENTS.md), the [product contract](docs/design.md), the
[seam index](docs/groom/index.md), and [handoff](docs/handoff.md). Feature
branches and opt-in controls remain independent. Later plans are re-groomed
only when they start; a stale future plan is a warning, not a reason to rewrite
all plans now.

```sh
make groom-check PYTHON=.venv/bin/python        # report; stale plans warn
make groom-check SEAM=0 PYTHON=.venv/bin/python # selected seam must be fresh
make gate-seam0 PYTHON=.venv/bin/python         # clean committed source only
```

The checker reads committed HEAD and needs complete Git history. Fetch full
history before checking a shallow clone. Missing/malformed metadata fails in
both modes. Dependencies are comma-separated literal repository-relative
paths; directories include descendants. Draft edits are not a re-groom:
commit changes and rerun. Move `Groomed-at` only after reviewing actual
dependency commits and code; see ADR 0001 for non-cascading bookkeeping.

The setup gate creates a temporary archived checkout and fresh venv, restores
the existing declared development dependencies if missing, then runs freshness,
lint, offline tests, builds, distribution and installed-wheel CLI checks.
It requires Python with venv/pip and Git, not an emulator or AWS account.
Run `python scripts/gate_seam0.py --evidence-dir /absolute/new-directory`
to retain logs elsewhere. Default evidence is ignored under `.gate-evidence/`;
keep sanitized durable copies for handoff. The disposable workspace is cleaned
up automatically. This gate is offline with respect to AWS, not dependency
downloads; dependency versions and the tested commit are recorded.

Core changes use separate assertion-failing RED and passing GREEN commits.
Tests have literal fixtures, `Catches:` docstrings and a declared budget.
Scan staged changes before every commit, for example:

```sh
git diff --cached --no-ext-diff | gitleaks stdin --no-banner --redact
```

Record PASS/FAIL gate evidence and as-built differences in the active seam,
then update the handoff. Unperformed human checks stay in
`docs/human-tasks.md`, explicitly unverified.

## Development

Use Python 3.11+ in a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m ruff check .
.venv/bin/python -m unittest discover -s tests/unit -v
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*
```

For emulator changes, also run the seven real integration tests with an existing
local image, and record the exact image/version, command and result:

```sh
AWS_EMULATOR_IMAGE=localhost/aws-emulator:1.0.322 \
  .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH="$PWD" AWS_EMULATOR_IMAGE=localhost/aws-emulator:1.0.322 \
  .venv/bin/python -m examples.three_tier.demo --strict-native
```

The strict command currently exits 1 for documented native gaps; it is not part
of the default CI success gate. Preserve its failing observations separately.
Do not add real credentials, private source, runtime logs with credentials,
emulator binaries or vendor packages. Disjoint ports are required for separate
runs. Do not run untrusted contributions against privileged container engines.

## Pull requests

Explain the behavior change, tests run and remaining limitations. Include
regressions for behavior changes. Make new bridges explicit and reject
undeclared routes. Keep package imports and CLI/configuration compatible within
patch releases. Contributions are licensed under the repository's MIT license.

## Releases

`project.version` in `pyproject.toml` is the version source of truth. Use
`MAJOR.MINOR.PATCH`, and tag the exact reviewed commit `vMAJOR.MINOR.PATCH`.
During 0.x, breaking changes increment MINOR; compatible fixes increment PATCH.
Never reuse a published version or move its tag; fix mistakes in a new release.

1. Update package version, changelog, README version and documented compatibility.
2. Run lint, offline unit tests, real integration and strict gap diagnostics.
3. Build/inspect the wheel and source distribution; install the wheel in a fresh
   environment and exercise the CLI. Keep examples/docs/tests in the source
   distribution and the library/license in the wheel.
4. Merge reviewed changes with green CI. Tag that main-branch commit and push
   the tag. Tag CI refuses a mismatch between SemVer, package version and tag.
5. The release job creates a draft GitHub release with a wheel, source
   distribution and `SHA256SUMS`. Inspect them, add results and limitations from
   the changelog, then publish the draft.

Actions are SHA-pinned, tokens are read-only except the tag-only draft-release
job, and dependency updates are proposed by Dependabot. There is no automatic
PyPI publishing, AWS authentication or emulator download.

Dependabot is the sole dependency updater; the repository disables overlapping
Renovate runs. Weekly minor/patch version updates are grouped by ecosystem,
while major updates and security updates remain separate review items.
Updates are not automatically merged. Changing the supported Python matrix or
the package-build interpreter is a deliberate compatibility decision, not a
routine dependency-range update.
