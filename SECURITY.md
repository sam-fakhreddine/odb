# Security policy

ODB runs trusted local test fixtures through a container engine. It is not a
security sandbox, and its bridges are not AWS authorization enforcement.
Never use production credentials or run untrusted code with this harness.

The loopback guards cover clients created by ODB, not arbitrary clients or
network access from application code. Docker support is a CLI selector;
Podman is the verified engine. Neither implies safe isolation from a hostile
workload or container engine.

## Reporting

Use GitHub's private vulnerability reporting on this repository's Security tab.
Do not disclose credentials, private application source or exploitable details
in public issues. For nonsensitive usage bugs and emulator limitations, use
ordinary issues with minimal synthetic reproductions.

Only the latest release is maintained during 0.x development. There is no
guaranteed response time or commercial support.
