# Gate 46 Package Authoring Contract V1

Contract ID: `EXPLORA_PROJECT_EXECUTION_RELEASE_V1`

## Purpose

This additive contract supplies project-specific executable/release information
that does not belong in intake Project Spec and is not a statistical result. It
is consumed together with one fingerprinted `READY_FOR_EXECUTION`
`EXPLORA_PROJECT_SPEC_V1`, accepted policy/Core registries, source metadata and a
B3-compatible release decision. Gate 46 defines the contract only; no builder is
implemented or authorized here.

## Required inputs

1. Exact Project Spec payload and fingerprint.
2. Source dataset fingerprint and authoritative questionnaire/datamap artifact
   fingerprints; physical data remains external.
3. `EXPLORA_PROJECT_EXECUTION_RELEASE_V1` with:
   - release spec identity/version and package identity/version;
   - source artifact authority and mapping-contract version;
   - explicit question role, structure and metric references;
   - explicit structure records containing all axes/bindings, category/option
     mappings, applicability, response-state, storage, completion, duplicate,
     exclusivity and denominator-scope semantics;
   - explicit MetricSpec selections from accepted Core formula/metric registries,
     including denominator, missing, weight, significance and parameters;
   - complete released WeightSpec records, default/override scope and explicit
     unweighted requests under B1;
   - one-question request records with explicit metrics, universe, weight,
     banner/filter members and significance reference;
   - significance family records with explicit members and sample relationship,
     while all test/eligibility/multiplicity constants come from B2;
   - explicit banner/filter members, dimensions and default behavior;
   - B3 release envelope and optional versioned corrective lineage.
4. Resolved human decisions referenced by stable decision IDs.
5. Accepted versions of B1, B2, B3, M2/M4/M5 and contract validators.

## Authoring algorithm contract

The future builder MUST:

1. Validate Project Spec as ready and verify its exact fingerprint.
2. Validate the Execution Release Spec schema, policy versions, B3 envelope and
   all cross-references before producing output.
3. Join logical variable IDs to physical `source_name` values exactly; labels or
   column-name resemblance are never binding authority.
4. Serialize one explicit released artifact for each configured record. It MUST
   NOT split a multi-question output request unless matching one-question ER
   request records are already human-approved.
5. Resolve policy fields only from accepted versioned contracts. It MUST NOT
   guess MetricSpec, RM semantics, weights, significance family, sample
   relationship, filters, banners or defaults.
6. Canonicalize each JSON artifact, compute deterministic artifact hashes, then
   create `MANIFEST.json` from the exact serialized bytes. Timestamp and human
   decision values come from the release envelope, never the wall clock.
7. Emit exactly the ten loader-required files for V1. Optional historical QA or
   deferred-candidate files are outside the generic package authority.
8. Validate the completed ZIP by loading it with the current loader and applying
   structural/reference/policy validators without executing analytical results.
9. Publish atomically only after all validation passes.

## Release rules

- Only a B3-authorized `RELEASED` package may be consumed by Core.
- AI may propose ER fields and evidence links. It may not convert a proposal to
  RELEASED configuration without the applicable B3 mode and decision evidence.
- B1 remains sole weight methodology authority. Missing/invalid weight config
  blocks release; it never becomes silently unweighted.
- B2 remains sole significance methodology authority. Unsupported inference is
  explicit; no substitute test or permissive fallback is allowed.
- Core registries remain sole formula authority. Authoring performs no
  percentages, bases, weighted bases, effective n, means, scores, significance,
  canonical results, observed source counts or eligibility calculations.
- Presentation labels may be copied as metadata but cannot alter analytical
  identity or values.

## Determinism

For identical normalized inputs and policy/contract versions, every semantic
artifact and `spec_hash` MUST be byte-stable. The ZIP container fingerprint may
only be considered deterministic if entry order, compression profile and entry
timestamps are frozen by the implementation contract. Any non-frozen packaging
metadata must be excluded from semantic identity and treated as an implementation
blocker until specified.

## Fail-closed conditions

Authoring fails before publication for any missing classification-A/D/E input,
unresolved critical ambiguity, missing human decision, unsupported structure or
operator, unknown formula/policy version, implicit request split, dangling or
duplicate reference, ambiguous physical binding, incomplete weight/significance
configuration, unauthorized default, hash mismatch, source-authority mismatch,
statistical-result field requested from the authoring layer, or incompatible
loader validation.

## Output authority

The package is configuration and release authority only. `materialize_project`
remains physical runtime authority; M2-M5/Core remain statistical authority;
Canonical Results remain result authority; Web/Excel remain presentation only.

## Genericity

The contract contains no project IDs, request IDs, variable names, metric
choices, weight choices or structure semantics tied to Benchmark A or ATLAS.
Those projects may instantiate the contract only through separate approved
inputs.

## Readiness decision

The contract is **READY FOR GENERIC PACKAGE BUILDER IMPLEMENTATION**. Project
Spec alone remains insufficient; implementation must require the additive ER
contract and human decisions defined here. Gate 46 does not authorize that
implementation.
