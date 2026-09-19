# B2 Core Significance Execution Implementation Review

## CURRENT STATE

Before Gate 39A, Canonical Results defined `SignificanceRelation`, and the execution
adapter accepted already-created relations, but Analytics Core did not calculate B2.
`src/reporter/significance.py` separately calculated display letters and remains legacy
presentation behavior rather than canonical authority.

## TARGET STATE

Analytics Core executes the frozen B2 pooled two-proportion z-test for deterministic,
released, independent, respondent-binary, unweighted comparison families and emits
authoritative `SignificanceRelation` records through canonical execution.

## GAP

The missing Core engine blocked Gate 39. Mean/Welch execution is still not implemented;
Gate 39A qualifies the explicitly required proportion branch only. Weighted, paired,
panel, RM-mention and other B2-unsupported methods retain explicit unsupported status.

## DECISION

Implement `B2_CORE_SIGNIFICANCE_V1` independently in `analytics_core`, using only the
Python standard library for production mathematics. Do not import or migrate reporter
logic, and do not modify M7 or Excel.

## IMPLEMENTATION

`ProportionComparisonInput` carries stable member/slice identities, integer respondent
counts, unweighted bases and declared assumptions. `execute_proportion_family` validates
the released `SignificanceSpec`, applies minimum-base and pooled expected-count gates,
computes the two-sided pooled z p-value, applies family-scoped Holm adjustment, assigns
canonical status/direction and emits deterministic IDs/provenance. `CanonicalExecutionContext`
can execute declared proportion families and rejects mixing them with supplied relations.

## B2 POLICY CONFORMANCE

- Confidence is restricted to 0.90, 0.95 or 0.99 by the frozen validator.
- Tests are two-sided and use `erfc(abs(z)/sqrt(2))`.
- Both unweighted bases must be at least 30.
- All four pooled expected success/failure counts must be at least 5.
- Ineligible pairs do not receive p-values or enter Holm.
- Weighted and non-independent inference are explicit `UNSUPPORTED` results.
- Direction comes from Core and is not inferred downstream.

## NUMERICAL VALIDATION

Production has no second statistical-package dependency. Tests independently compare
raw p-values with `statsmodels.stats.proportion.proportions_ztest` to 1e-15, and cover
Holm monotonicity, direction symmetry, 90/95/99 decisions, non-significance, minimum
base, sparse expected counts and degenerate variance.

## CANONICAL RESULTS INTEGRATION

A real `CanonicalExecutionContext` with a `ProportionFamilyRequest` executes B2 during
canonical assembly and emits a validated `SignificanceRelation` containing stable
comparison identity, confidence, status, p-values, direction and provenance.

## LEGACY REPORTER RELATIONSHIP

Legacy reporter significance remains unchanged for compatibility. It is not imported
by Core and is not the canonical authority. Migration/removal is separate future work.

## VALIDATION

- Focused Gate 39A: 25 passed / 0 failed / 0 skipped.
- Analytics Core/B1/B2: 184 passed / 0 failed / 0 skipped.
- Canonical regression: 214 passed / 0 failed / 0 skipped.
- Gate 38 regression: 20 passed / 0 failed / 0 skipped.
- Full regression: 796 passed / 0 failed / 0 skipped; increase from 771 is exactly 25.
- Unexpected numerical and canonical deltas: none outside the controlled new scenario.

## BLOCKERS

None for the B2 proportion-engine prerequisite.

## WARNINGS

- Legacy reporter letter calculation still exists; canonical Core output is now the
  official analytical authority, but reporter migration is not claimed.
- Reason and diagnostics are retained in structured provenance references because the
  frozen `SignificanceRelation` schema has no dedicated reason/diagnostics fields.

## COVERAGE GAPS

- Welch mean execution is not implemented or qualified in this gate.
- B2-deferred and unsupported methods remain unavailable by design.

## GATE 39 RESUME READINESS

YES for controlled proportion-significance presentation qualification after human
review and Git adoption of this exact Gate 39A implementation.

## NEXT MILESTONE AUTHORIZED: NO
