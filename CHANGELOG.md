# Changelog

All notable changes are recorded here. Releases follow Semantic Versioning.

## Unreleased

### Added

- Strict schema-first Python inventory models with Pydantic 2, immutable
  snapshots, safe parsing diagnostics and generated versioned JSON Schema.
  Opt in with `Harness(..., strict_manifest=True)` or `--strict-manifest`;
  legacy defaults and published v0.1.0 assets remain unchanged.
- Strict mypy checks with positive/four-error negative consumers and a
  packaged `py.typed` marker. The check scope is contracts/schema, not the
  entire legacy runtime. Offline CI and the selected seam gate detect schema
  drift and verify typed consumers against an isolated installed wheel.

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

## [0.3.0](https://github.com/sam-fakhreddine/odb/compare/v0.2.0...v0.3.0) (2026-11-16)


### Features

* **evidence:** GREEN offline evidence contract ([a5d5d0c](https://github.com/sam-fakhreddine/odb/commit/a5d5d0c901c90de95bdf6aa1557cc772c1f4f296))
* **evidence:** strict offline evidence contract (seam 1) ([d29c5f1](https://github.com/sam-fakhreddine/odb/commit/d29c5f14a6b80595c66f5d855d3a37e41220c0b7))
* **types:** GREEN strict inventory contracts ([090819a](https://github.com/sam-fakhreddine/odb/commit/090819a5c4cb7fb1bc084e197cbcb25b7c3ad525))


### Bug Fixes

* **types:** GREEN close generated inventory mapping schemas ([cddacfd](https://github.com/sam-fakhreddine/odb/commit/cddacfd38c358245ee6f3b1de8332875869ec41d))
* **types:** reject invalid inventory mapping keys in schema ([da382f9](https://github.com/sam-fakhreddine/odb/commit/da382f9462c18abda459d2fb507bce051dfe9b16))

## [0.2.0](https://github.com/sam-fakhreddine/odb/compare/v0.1.0...v0.2.0) (2026-11-15)


### Features

* **groom:** GREEN enforce committed seam freshness ([9b65208](https://github.com/sam-fakhreddine/odb/commit/9b652081c41853f3eedced5d977084f52e90fb93))
* **release:** propose semantic versions without publishing ([51fb1b8](https://github.com/sam-fakhreddine/odb/commit/51fb1b8e3287716d756a802d4ae49946e3585f28))


### Bug Fixes

* **gate:** resolve macOS temporary directory aliases ([46f6f77](https://github.com/sam-fakhreddine/odb/commit/46f6f776ce6e92622695ac5f5f977c4b8aa759b7))

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
