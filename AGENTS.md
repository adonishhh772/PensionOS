# PensionOS Data Onboarding Agents

This repo is a bounded implementation of the PensionOS Data Onboarding & Resolution Factory specification.

## Operating principles

- Configure, do not customise.
- Treat pension-critical values as governed and evidence-backed.
- Apply the smallest safe block, not a whole scheme halt.
- Keep provenance, authority, and data-state semantics explicit.
- Build in PR slices and stop after each slice.

## Current slice

PR-01 is the active slice:

- source registry and lifecycle
- source authority policy skeleton
- onboarding batch lifecycle
- repository ports
- domain validation

Do not add file parsing, AI mapping, exception clustering, or final promotion logic until the slice is complete and validated.

## Working conventions

- Python domain models should be dataclasses or value objects.
- Use explicit enums for status and state transitions.
- Repository boundaries should be interface-based.
- Tests must use synthetic data and avoid live member PII.
- Any AI assistance must be limited to suggestions and never auto-correct material pension values.
