# Gate 47 Generic Package Builder Implementation Review

## Current State

Gate 47 implements the Gate 46 additive architecture on branch
`feature/gate47-generic-released-package-builder`. Project Spec V1 is unchanged.

## Target State And Gap

The target was deterministic Project Spec + ER to released package authoring and
reuse of the existing loader, materializer, compiler and productive runtime. The
missing builder is implemented. A non-circular compiler identity path and removal
of one Benchmark-specific universe reconstruction constant were the only runtime
integration changes.

## Decision And Implementation

`src/package_authoring/contract.py` is the fail-closed ER authority.
`src/package_authoring/builder.py` maps approved configuration into exactly ten
released artifacts, computes hashes, freezes ZIP metadata, verifies the loader,
and publishes atomically. Existing package-hash metadata remains accepted for
historical packages; new packages bind by the manifest's exact Project Spec
fingerprint plus questionnaire identity.

## Validation

Pre-corrective focused coverage contained 45 collected Gate 47 cases, including deterministic
bytes, exact inventory, source mismatch, no replacement, loader/materialization,
compiler and Gate 45 runtime. The synthetic runtime creates Canonical Results and
Web output without Legacy fallback. Relevant and full regression evidence is
recorded in `GATE47_GENERIC_PACKAGE_BUILDER_CHECKPOINT.json` after execution.

Corrective focused coverage is 60/0/0, relevant regression is 638/0/0, and full
repository regression is 1018/0/0 (passed/failed/skipped).

## Review Decision

The initial Human Review result was FAIL / CORRECTIVE REMEDIATION REQUIRED at
`daca3656df8d27940eb38a5ef72ca6eca9013ee9`.

## Corrective Resolution

- B-G47-01: ER requests now bind to `output_request_ref`; exact explicit
  multi-question coverage is required, with no generated IDs or Cartesian split.
- B-G47-02: `package.internal_project_name` is required and is the sole serialized
  authority; Project Spec display text is not used.
- B-G47-03: non-empty released Significance Specs combine ER project choices with
  machine-readable, validated `SignificanceSpec` B2 V1 methodology.
- B-G47-04: released WeightSpecs and bound raw values now reach existing M3;
  project default, request override and explicit unweighted paths are tested.
  Weight registry overrides are derived from explicit requests.

Corrective status is PASS pending Human Re-review. No PR is created and no merge
is performed. Gate 48 and ATLAS productive execution are not authorized.

## Final Corrective Resolution

B-G47-05 is resolved by deriving `analysis_specific_overrides` solely from ER
`weight_choice == REQUEST_OVERRIDE`. The registry now preserves an explicit
override even when its `weight_ref` equals the project default. `PROJECT_DEFAULT`
and `EXPLICITLY_UNWEIGHTED` remain distinct registry paths. Existing M3 selection
is unchanged. The supported-profile matrix also states separately that
`PARENT_RM` and `MENTION` are not yet qualified.

Final corrective evidence is 66/0/0 focused, 644/0/0 relevant, and 1024/0/0
full repository regression (passed/failed/skipped).
