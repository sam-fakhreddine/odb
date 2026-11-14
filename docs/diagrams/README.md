# Architecture diagrams

These diagrams describe the source on `main`. They are documentation, not new
test results or a claim of AWS parity. The existing v0.1.0 release is unchanged.

| View | Preview | Vector | Print | Editable sources |
| --- | --- | --- | --- | --- |
| ODB and independent native processes | [PNG](architecture_1_flowchart_emulator_interaction.png) | [SVG](architecture_1_flowchart_emulator_interaction.svg) | [PDF](architecture_1_flowchart_emulator_interaction.pdf) | [Mermaid](architecture_1_flowchart_emulator_interaction.mmd), [design JSON](architecture_1_flowchart_emulator_interaction.design.json) |
| Three-account example and its two seams | [PNG](architecture_2_flowchart_three_account_example.png) | [SVG](architecture_2_flowchart_three_account_example.svg) | [PDF](architecture_2_flowchart_three_account_example.pdf) | [Mermaid](architecture_2_flowchart_three_account_example.mmd), [design JSON](architecture_2_flowchart_three_account_example.design.json) |

## Reading the boundaries

The first diagram shows the generic harness: separate emulator processes,
runtime-specific SDK clients and opt-in bridges. Every process still reports
native account `000000000000`; logical identity includes its selected runtime.
Role selection is not STS authorization. The loopback client guard is not an
OS network sandbox.

The second shows the runnable [three-account example](../../examples/three_tier/README.md).
Static requests reach the real emulator CloudFront listener and private S3.
An explicit API relay selects the application runtime and invokes its native
Lambda. A second fixture checks owner RAM/subnet records against separately
created participant resources and Lambda configuration. Those resources do not
become a physically shared VPC.

On the tested emulator 1.0.322, direct cross-process CloudFront/Lambda forwarding
returns 502, RAM shared subnets are not visible in the participant process and
Lambda accepts nonexistent subnet IDs. These remain strict-native failures;
the adapted path does not conceal or fix them. Diagnostics are measured on
each run, so results may change with another emulator version.

## Editing and rendering

Mermaid is the authority for nodes, relationships and nesting. The adjacent
design JSON controls presentation. Change the pair together, validate and
regenerate all three exports, then inspect the PNG for clipping, overlaps and
readable labels. PNGs are 1920 x 1080; SVGs and PDFs retain the measured vector
canvas.

These exports were produced with the separate EE Mermaid infographic renderer
(`ee-mermaid-dev`, `aws-architecture` preset). That renderer is not an ODB
runtime or development dependency and is not bundled here. Its wrapper requires
Node.js, uv/Python 3.12, Mermaid CLI and a compatible headless Chromium shell.
With that tool installed, run from the ODB repository root:

```sh
# Set EE_MERMAID_DIR to the installed skill directory containing scripts/.
# Set CHROME_PATH and PUPPETEER_EXECUTABLE_PATH to the headless shell if needed.
node "$EE_MERMAID_DIR/scripts/render_infographic.ts" \
  --input docs/diagrams/architecture_1_flowchart_emulator_interaction.mmd \
  --design docs/diagrams/architecture_1_flowchart_emulator_interaction.design.json \
  --out /tmp/odb-emulator-interaction --formats svg,png,pdf

node "$EE_MERMAID_DIR/scripts/render_infographic.ts" \
  --input docs/diagrams/architecture_2_flowchart_three_account_example.mmd \
  --design docs/diagrams/architecture_2_flowchart_three_account_example.design.json \
  --out /tmp/odb-three-account --formats svg,png,pdf
```

The wrapper runs resilient Mermaid validation before infographic rendering.
Copy only the inspected SVG/PNG/PDF exports back to this directory. Validation
reports, render diagnostics, caches and the renderer's bundled HTML are not
publication artifacts.

## Attribution

ODB-authored diagram sources and documentation use the repository's MIT
license. The vector exports embed Roboto Condensed and Inter fonts under the
SIL Open Font License; preserve [Roboto Condensed's notice](RobotoCondensed-OFL.txt)
and [Inter's notice](Inter-OFL.txt) when redistributing them. The diagrams use
generic line icons rather than AWS service-logo assets.
