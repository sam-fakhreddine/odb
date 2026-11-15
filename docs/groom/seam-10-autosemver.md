# Seam 10: opt-in automatic version proposals

Selected 2026-11-15: owner requested "we need autosemver". Branch:
`feature/auto-semver`, based on the independent seam workflow foundation.

## Outcomes and budget

1. A conventional-commit proposal derives from published v0.1.0, increments
   major/minor/patch under the existing pre-1.0 compatibility policy, and
   updates project metadata, changelog and README references.
2. The workflow does not create tags or releases, requires explicit opt-in and
   a configured token, and does not change existing release behavior by default.
3. Package checks and the manual reviewed tag/draft-release flow remain intact.

Configuration/glue seam, not a new local trust-boundary implementation: validate
actual pinned release-please versioning and updater behavior against literal
examples; validate configuration and workflow guard with focused offline tests;
run lint, offline suite and package checks in a disposable committed-source gate.
No artificial RED commit for a third-party action; failure controls test the
configuration and upstream engine directly. Do not claim a live GitHub run or
release unless performed with separate authorization.
