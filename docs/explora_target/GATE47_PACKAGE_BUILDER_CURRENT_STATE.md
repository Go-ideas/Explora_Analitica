# Gate 47 Package Builder Current State

## Current State

Gate 46 is CLOSED / ACCEPTED / MERGED through PR #19 at official main
`2608aaf583217a998308a54ba3854ca1be82c254`. The current loader consumes exactly
the ten names in `canonical_materialization.materializer.PACKAGE_FILES`, requires
a RELEASED manifest, preserves package `default_execution_mode=LEGACY`, and
rejects productive dual-run metadata. Materialization binds released physical
variables and validates domains and references before M2-M5 execution.

## Target State

A project-neutral authoring boundary accepts one READY Project Spec, one accepted
`EXPLORA_PROJECT_EXECUTION_RELEASE_V1`, source identity, accepted B1/B2/B3/Core
identities, and a manual B3 decision. It publishes one deterministic ten-file ZIP
only after contract, hash, deterministic-container and current-loader validation.

## Gap

Before Gate 47 there was no executable ER validator or package builder. The Gate
45 compiler also required a ZIP hash inside its own upstream Project Spec, and
the canonical orchestrator reconstructed every question with a Benchmark-specific
universe ID. Both prevented a generic authored-package flow.

## Decision

Implement authoring in isolated `src/package_authoring`. Preserve the historical
compiler path while accepting the builder manifest's exact Project Spec
fingerprint as the non-circular package binding. Reconstruct question universe
identity from the released package. Do not alter analytical mathematics, loader
requirements, Project Spec schema, or Legacy rollback.

## Implementation

The implementation validates explicit structures, formulas, requests, weights,
banners, filters, significance families, source authority and B3 release. It
canonicalizes JSON, hashes semantic records without self-hashing, freezes ZIP
order/compression/time/permissions, verifies source bytes when supplied, performs
the current loader round trip, and atomically renames the completed archive.

## Validation

The synthetic proof authors a non-customer SAV-bound project, loads and
materializes the package, compiles it, executes CANONICAL_V1 through the existing
Gate 45 productive runtime, and emits configured Web output. ATLAS productive
execution is not attempted. Final regression counts are recorded in the Gate 47
checkpoint and implementation review.
