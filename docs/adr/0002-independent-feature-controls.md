# ADR 0002: Independent feature branches and truthful controls

Date: 2026-11-15. Status: accepted.

## Context

Owner, 2026-11-14: "each is a feature branch / flag".
Owner, 2026-11-15: "and it shows where it had to be faked and to check actual aws".

## Decision

Use one branch per feature, with independently selectable rollout. Runtime
features are opt-in and retain current defaults. CI scheduling uses a manual
workflow or explicit repository control, not a meaningless runtime flag.
The setup branch adds development machinery only and needs no runtime flag.

Reports must separate outcome, provenance, coverage and AWS validation.
Adapters must never silently satisfy native assertions. Tracing is optional
and cannot disable assertions when off. Native capability probes never silently
activate an adapter. Real AWS comparison requires separate explicit approval.

## Consequences

Features can share a stable evidence contract without sharing activation.
Subsequent seams within a feature may stay on its branch; dependencies are
recorded explicitly, not assumed from row order. No native Organizations state,
SCP enforcement, cross-account IAM or networking is promised by imported state.
