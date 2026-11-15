Groomed-at: 88681285f3083b91aa3e2a88b1b62fe84c6c925d
Depends-on: docs/design.md, docs/adr, docs/groom/seam-10-autosemver.md, .github/workflows/ci.yml, pyproject.toml, README.md, CONTRIBUTING.md
Re-groomed: 2026-11-15; select automatic version proposals after the v0.1.0 release.

# Seam 10 worker brief

Use the maintained release-please Python strategy, pinned by full action SHA.
Bootstrap from the published v0.1.0 tag's commit. Preserve the existing
pre-1.0 policy: breaking changes increase minor; compatible fixes increase
patch. Conventional features increase minor. The proposal updates package
version, changelog and annotated README versions.

Automatic release-PR proposals require explicit repository opt-in. The workflow
must never create tags or releases; existing review, tag, build and draft release
steps remain separate. Use a configured token capable of triggering CI for
generated PRs; fail explicitly if it is absent. No credentials in source.
Verify pinned upstream versioning/updater behavior with real library tests,
configuration shape, existing checks and a clean disposable gate. Do not push
or create a PR or release.
