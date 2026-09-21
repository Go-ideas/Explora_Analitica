# Gate 44 — CODEX HANDOFF

## Repository

`Go-ideas/Explora_Analitica`

## Authoritative starting main

`c6b40f7f4023325bc6dbc4ad9939ef91744a8c3f`

## Feature branch

`feature/gate44-first-productive-e2e`

Do not work directly on main.

## Objective

Implement the first productive EXPLORA project end-to-end:

PROJECT PACKAGE
→ EXPLORA_PROJECT_SPEC_V1
→ READY_FOR_EXECUTION
→ deterministic execution binding
→ EXPLORA Core
→ Canonical Results
→ Canonical Materialization
→ Web
→ Excel
→ QA
→ Provenance
→ Release Package

## Productive candidate

Use Benchmark A / FUNSMX 297140 only if authoritative source inputs required for genuine re-execution are available.

Accepted identity evidence includes:

`MENTION / PARENT_RM / STR_Q_DELIVERY_APPS_RM_V1`

Benchmark-specific behavior must never be hardcoded into Core.

If authoritative inputs are missing, stop with:

`GATE 44 STATUS = BLOCKED`

Do not reconstruct source data from Canonical Results and do not substitute synthetic fixtures while calling the run productive.

## Mandatory pre-implementation audit

Before code changes:

1. Verify branch ancestry from the authoritative main SHA.
2. Verify clean worktree.
3. Audit:
   - project_intake
   - contracts.models.ProjectSpec
   - analytics_core
   - canonical execution adapter
   - canonical_materialization
   - web_canonical
   - excel_renderer
   - production_masters
   - Benchmark A source/release artifacts
   - QA/release machinery
   - provenance/fingerprinting
4. Update `GATE44_FIRST_PRODUCTIVE_E2E_CURRENT_STATE.md` with the exact boundary and manual translations currently required.
5. Do not redesign accepted contracts before documenting current behavior.

## Implementation boundary

Implement only the narrowest deterministic Project Spec → released execution/materialization bridge required for Gate 44.

It may translate:

- project identity
- dataset binding
- question/structure/category identities
- universes
- B1-compatible weights
- banners
- filters
- B2 significance requests
- output intent
- approved decisions
- provenance references

It must not calculate percentages, bases, weighted bases, effective n, means, scores or significance.

## Fail closed

Fail closed for any non-ready Project Spec, unresolved material ambiguity, unreleased AI decision, source fingerprint mismatch, unresolved references, unsupported structure, unrepresentable universe, B1/B2 violation, unresolved banner/filter binding, unsupported output intent or incomplete provenance.

No silent repair.
No silent assumption.
No silent downgrade.
No silent Legacy fallback.

## Runtime authority

Use `CANONICAL_V1`.

Core is statistical authority.
Canonical Results are the official analytical results.
Web and Excel are presentation consumers of the same released Canonical Results.

## Web requirement

Generate productive Web output using the accepted canonical path.

For overlapping validation results:

`Web == Canonical Results`

## Excel requirement

Use the qualified Production Master 1.2.0.

Expected master SHA-256:

`f3a11f291b6c661f0c937e9c95d7f227c351d7261b2e01aa44dfd4167d5c869c`

Expected VBA SHA-256:

`0f879b60ed12315085bc722c3f59163f86ce24609e3ba6ad379069c44779b758`

For overlapping validation results:

`Excel physical read-back == Canonical Results`

Preserve VBA exactly.

Do not expand scope to unrestricted charts, pivots, slicers, arbitrary worksheet growth, signatures, external connections or general-purpose Excel generation.

## Significance

Where exercised:

Core/B2 calculates → Canonical Results transports → Web/Excel present.

No Excel/VBA significance mathematics.

## Required release evidence

Populate the Gate 44 evidence package with:

- config/project_spec.json
- accepted human decisions if any
- canonical execution/materialization manifests
- released Canonical Results
- reproducible Web output/evidence
- rendered productive .xlsm
- QA parity/read-back evidence
- provenance fingerprints and runtime identities

Do not commit confidential customer raw data unless specifically authorized. External inputs may be referenced by secure provenance and hashes.

## Determinism

Execute the productive pipeline at least twice with identical accepted inputs.

Require exact logical equality for source fingerprints, Project Spec fingerprint, compiled binding, Canonical Results fingerprint, materialization fingerprint, RenderPlan fingerprint, controlled Excel read-back and relevant Web logical output.

Do not require whole rendered XLSM byte identity unless an accepted contract guarantees it.

## Gate 44 focused validation

Cover at minimum:

- authoritative source identity
- Project Spec validation
- READY_FOR_EXECUTION enforcement
- deterministic compilation
- unsupported compilation fail-closed
- CANONICAL_V1 execution
- no Legacy fallback
- Canonical Materialization
- Canonical Results authority
- Web canonical consumption
- Excel canonical consumption
- Production Master identity
- VBA preservation
- Dynamic Region read-back where exercised
- significance transport where exercised
- Canonical ↔ Web exact parity
- Canonical ↔ Excel exact parity
- Web ↔ Excel exact parity
- provenance completeness
- deterministic rerun
- no partial release on failure
- B1/B2/B3 preservation
- protected M2–M7 semantics
- full regression

Unexpected skips are blockers.
Unexpected numerical deltas are blockers.

## Required final report

Update:

- `docs/explora_target/GATE44_FIRST_PRODUCTIVE_E2E_IMPLEMENTATION_REVIEW.md`
- `docs/explora_target/GATE44_FIRST_PRODUCTIVE_E2E_CHECKPOINT.json`

Report feature HEAD, files added/modified, test counts, parity, hashes, provenance, blockers and warnings.

Do not merge.

Stop after implementation review for Human Review.
