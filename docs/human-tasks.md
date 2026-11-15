# Human-only tasks

These do not block automated local seams. Pending rows mean not verified, not
passed. No row authorizes an agent to spend money, access an account or publish.

| ID | Task | Why human action is needed | Status |
| --- | --- | --- | --- |
| H1 | Approve exact real-AWS sandbox accounts, region, operations, limits, duration and cleanup owner | Account authority and cost authorization | Pending; no AWS execution authorized |
| H2 | Approve publication of setup/feature branches and PRs when ready | Public action and review ownership | Pending; local setup only |
| H3 | Confirm emulator acquisition/authenticity and redistribution policy before hosted native CI | External distribution/runner policy | Pending; no native CI claim |
| H4 | Supply only sanitized or synthetic organization inputs | Validation cannot establish that identifiers/policies are safe to publish | Pending; examples must be synthetic |

Other Python/platform checks are automatable verification work, not human-only
gates. Unsupported/unrun environments remain explicitly unverified.
