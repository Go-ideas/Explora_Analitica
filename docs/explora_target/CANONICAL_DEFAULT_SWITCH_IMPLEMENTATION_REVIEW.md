# Canonical Default Switch Implementation Review

Gate 32 baseline: main 6c0bf08895603b2b80b6a3c5fb5e1fea744b9d30.
Branch: feature/canonical-default-switch. Starting worktree: clean.

## CURRENT STATE / RUNTIME RESOLUTION BEFORE

Recorded before source changes: analytics_core/mode.py is the authoritative Core
resolver. An explicit selector wins over EXPLORA_ANALYTICS_ENGINE; when both are
absent it returns LEGACY. Empty/invalid selectors raise ExecutionModeError.
CANONICAL_V1 is the existing canonical enum value; CANONICAL is currently invalid.
The two Web pages additionally default missing settings to LEGACY and the shared
runtime selectbox initially selects LEGACY. Those local defaults bypass Core's
environment setting. The runner already accepts CanonicalResult and validates
request binding; missing canonical input raises CanonicalResultRequiredError.
There is no accepted automatic Legacy fallback.

The released Benchmark A package records historical default_execution_mode=LEGACY.
That release metadata and its materialization validation are frozen; they do not
select the current runner runtime. Canonical cache keys have a canonical-only
default appropriate to that API, not an independent general runtime resolver.

## TARGET STATE

Unspecified selector and absent environment resolve to CANONICAL_V1. CANONICAL is
an authorized spelling of that same mode. Explicit LEGACY, CORE_WRAPPER,
CANONICAL_V1 and DUAL_RUN retain their dispatch paths. Web defaults use the same
resolver. No canonical inputs, analytical formulas or release metadata change.

## IMPLEMENTATION / RUNTIME RESOLUTION AFTER

The resolver now returns CANONICAL_V1 when explicit input and the environment
selector are absent. CANONICAL normalizes to CANONICAL_V1 in this resolver only;
the frozen ExecutionMode enum is unchanged. Explicit selection still wins over
the environment. Empty and unknown values still raise ExecutionModeError.

Both Web pages resolve missing settings through resolve_execution_mode. The
existing runtime control obtains its initial selection from that same resolver.
Its choices derive from the unchanged enum, including the already-supported
CORE_WRAPPER compatibility runtime, so an environment override can be represented
without a competing default or fallback. Existing stored explicit selections
remain explicit. No Web presentation or analytical capability was added.

### Files Added

* docs/explora_target/CANONICAL_DEFAULT_SWITCH_IMPLEMENTATION_REVIEW.md
* explora_web_reporter/scripts/validate_canonical_default_switch.py
* explora_web_reporter/tests/test_canonical_default_switch.py
* explora_web_reporter/tests/test_canonical_default_switch_benchmark_a.py

### Files Modified

* explora_web_reporter/src/analytics_core/mode.py: default and selector alias.
* explora_web_reporter/src/ui/page_04_reporter.py: centralized runtime selection.
* explora_web_reporter/src/ui/page_05_significance.py: centralized runtime selection.
* explora_web_reporter/tests/test_core_execution_mode.py: intended default assertion
  and replacement of the now-authorized CANONICAL invalid-selector example.
* explora_web_reporter/tests/test_m6_execution_modes.py: explicit Legacy regression.
* explora_web_reporter/tests/test_weight_runtime.py: only the global default
  assertion and its test name; unweighted-base expectations are unchanged.

Files deleted: NONE. Protected Core/M6 runtime-selection sites are changed only
as authorized for the default switch. A baseline diff confirms that contracts,
universe, weights, structures, execution adapter, runner, materialization, request
binding, comparison and canonical provenance code are unchanged. No formulas,
statistical semantics or production project/benchmark rules were added.

## FAIL-CLOSED BEHAVIOR

The unchanged runner exposes missing or incompatible CanonicalResult failures.
Changing the default does not materialize a project automatically, add an execution
adapter or retry through Legacy. Invalid selectors remain errors.

## ROLLBACK

Select mode="LEGACY" explicitly, use the existing Web runtime selector, or set
EXPLORA_ANALYTICS_ENGINE=LEGACY for requests without an explicit selector. No code
restoration is required. Explicit request selection remains higher precedence.

## TEST EVIDENCE / BENCHMARK A EVIDENCE / REGRESSION

CDS-001 through CDS-012: PASS individually. These cover default/explicit selection,
real DUAL_RUN comparison, invalid selectors, missing and incompatible canonical
inputs without invoking Legacy, actual explicit Legacy output, exact default vs
explicit equivalence, determinism, existing session metadata, project independence
and unchanged CanonicalResult snapshots. Additional cases cover environment
precedence, empty environment rejection, enum-valued selectors and both Web sites.

| Scope | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Default switch resolver / CDS tests | 17 | 0 | 0 |
| Default switch Benchmark A tests | 9 | 0 | 0 |
| Gate 19 focused | 38 | 0 | 0 |
| Canonical Materialization | 51 | 0 | 0 |
| Full regression | 602 | 0 | 0 |

The reference was 576; the exact increase is 26 new tests (17 + 9). Existing test
counts were not reduced. Tests use controlled external basetemp under
C:/Users/conta/gate32_temp. Full JUnit evidence:
C:/Users/conta/gate32_temp/gate32_full_regression.xml.

All five Benchmark A requests passed implicit canonical, explicit CANONICAL,
explicit LEGACY and DUAL_RUN. Default results are exactly the explicit canonical
results with unchanged fingerprints and snapshots. Explicit Legacy summaries
match the actual Legacy side of DUAL_RUN. The accepted comparison set remains
40 / 4 / 4 / 40 / 6 records, 94 total, all exact PARITY without tolerances or
classification overrides. BA-03 remains MENTION / PARENT_RM /
STR_Q_DELIVERY_APPS_RM_V1. Repeated complete validation outputs are deterministic.
Unexpected numerical/structural deltas, unexplained differences, potential
regressions and silent fallbacks: NONE. Benchmark package and runtime fingerprints
remain those accepted by Gate 19; no release artifact was modified.

The added validation script writes new external evidence, preserving earlier
Gate 19 artifacts. Committed-head Benchmark evidence destination:
_gate19_evidence/gate32_canonical_default_switch_validation_20260917.json.
It retains the full Gate 19 comparison/provenance plus requested/resolved modes,
canonical request/result identities and explicit Legacy summary comparisons.

## PROVENANCE

The existing CanonicalResult contains project, dataset, request, result and
configuration provenance. Web AnalysisSessionBinding records resolved mode and
result identities; DUAL_RUN observability records execution_mode. These structures
are preserved, without mutating frozen result snapshots to add runtime fields.
CDS-010 verifies the existing session metadata; the four-path Benchmark records
explicitly demonstrate canonical attribution and preserved result fingerprints.
Canonical results and the full accepted comparison provenance remain reconstructable
from source/package/runtime identities and released configuration. Provenance:
COMPLETE. Runtime spelling aliases do not create new analytical identities.

## KNOWN LIMITATIONS / BLOCKERS / WARNINGS

Canonical dispatch requires accepted canonical input. Existing Legacy-only saved
projects must explicitly select LEGACY until canonical inputs are supplied. Saved
explicit Web selections remain explicit; the switch applies to unspecified input.
The switch does not add materialization-to-Web orchestration. A released input is
still required by the frozen canonical execution path. Environment overrides
remain authoritative when no per-request selector exists. Historical release
metadata saying LEGACY is retained and is not the live default resolver.

Blockers: NONE. Warning: Legacy-only projects require explicit LEGACY or accepted
canonical inputs. The changes are local to the feature branch, ready for human
implementation review; main was not edited and no merge or push was performed.
M7 and productive Excel integration were not started.
