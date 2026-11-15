# Changelog

All notable changes are recorded here. Releases follow Semantic Versioning.

## Unreleased

### Documentation

- Establish seam development contracts, ADRs, setup/evidence grooming, handoff
  and human-task records, with a history-aware freshness check and offline
  disposable setup gate. Proposed runtime features remain unimplemented.
- Add two architecture infographics covering ODB/native-emulator interaction
  and the three-account example, with explicit fixture boundaries and native
  failure diagnostics. Include PNG, SVG, PDF and editable Mermaid/design pairs.

### Maintenance

- Permit setuptools 84 and Twine 7 while retaining the existing lower bounds.
- Use Dependabot as the sole updater, group weekly minor/patch version updates
  by ecosystem and keep major/security updates separately reviewable.
- Retain the Python 3.12 package-build baseline and Python 3.11-3.14 test matrix.
  Published v0.1.0 artifacts and its tag are unchanged.

## 0.1.0 - 2026-11-14

Initial MIT-licensed release of ODB (Ol' Dirty Bridge).

### Added

- Independent local AWS Emulator processes selected by configurable logical
  account inventories, regions, local images and explicit routes.
- Private-CA HTTPS clients, loopback endpoint guards, generated local credentials,
  ambient-profile isolation and owned-resource cleanup.
- Explicit simulated role selection, cross-account event relay and bounded,
  byte-verified object transfer with failure/uncertainty receipts.
- Three-tier example: native private S3/CloudFront site, business Lambda and
  owner VPC/subnet/RAM metadata, with explicit API/subnet fixture seams.
- Native integration tests and mandatory broken-plumbing controls.
- Offline unit CI for Python 3.11-3.14, distribution validation and versioned
  GitHub release assets with SHA-256 checksums.

### Known limitations

- Logical account IDs do not change native account identity. Routing is not
  AWS authorization or physical/network isolation.
- On the tested emulator 1.0.322, cross-process CloudFront/Lambda URL forwarding
  returns 502, RAM shared subnets are not visible in another process, and Lambda
  accepts nonexistent subnet IDs. Strict native mode fails rather than hiding
  these gaps.
- Integration was verified locally with Podman on macOS/ARM64 and boto3 1.43.73.
  Hosted CI does not contain emulator binaries or run those integrations.
- No emulator image/RPM, AWS service, private application, PyPI publication or
  production-support guarantee is included.
