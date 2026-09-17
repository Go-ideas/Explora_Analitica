# Gate 19 Corrective Implementation Review

Gate 19 remains OPEN / NOT ACCEPTED pending corrective review. This branch is
based on main e465457d7e6e23d13bea8d43955c1a84790f5d65.

## CURRENT STATE

The first productive attempt executed Legacy and Canonical successfully but
produced zero comparable records. BA-01 through BA-03 returned REVIEW_REQUIRED
because released category/option IDs did not match display rows. BA-04 and BA-05
failed request binding. The absence of numerical deltas in that attempt did not
establish parity. Its external evidence is retained unchanged at
`_gate19_evidence/gate19_productive_dual_run_validation_evidence.json`.

## TARGET STATE

The accepted Benchmark A V1.0.1 package must execute through the actual DUAL_RUN
runner with identifiable records on both sides, actual value comparisons,
reconstructable provenance and deterministic identities. Zero comparable records
cannot establish parity. LEGACY remains the default.

## GAP

### B-G19-01

Canonical Result option/category IDs -> runner._dual_run_comparison ->
legacy_comparison_records_from_report -> ReportResult.summary -> ComparisonRecord.

Legacy source tables retain `codigo_respuesta` and `variable` (RU) or
`variable_origen` (RM). `_prepare_data` preserves those columns, but
frequency_summary/rm_summary aggregate by `(banner, respuesta)` and omit physical
identity from the summary. Canonical IDs therefore cannot be resolved directly.
Parsing or matching display labels cannot recover authoritative identity.

### B-G19-02

Release filter_ref/member_ids -> materialization._slices -> Runtime Input ->
m5_request_snapshot -> M6 validate_request_binding -> execution request.

The request snapshot contains `{filter_ref: tuple(member_ids)}`; the slice contains
`filter_ref:member1|member2`, its configuration records the same restriction, and
the filtered non-banner slice is not an unfiltered total. The generic Web path
instead derives `filter_field_value` tokens and requires is_total=True.

### B-G19-03

Release banner_ref/member_ids -> materialization._slices -> Runtime Input ->
m5_request_snapshot -> M6 validate_request_binding -> execution request.

The request snapshot contains `{banner_ref, member_ids}`. Materialized slices use
the released dimension ID/member ID and retain banner_ref/raw_value in
configuration; this request emits members only. The generic Web path interprets
dictionary keys as dimensions and additionally demands a total slice. Those
representations are different accepted interface shapes, not a reason to change
the analytical universe or calculate additional results in Web.

## DECISION

Preserve physical identity alongside Legacy output and bridge it using released
configuration. Select the existing materialization compatibility profile for
materialized coverage validation. Keep the established Web validation path for
other profiles. Reject unresolved and contradictory identities.

## IMPLEMENTATION

* reporter/tabulator.py adds ReportResult.identity_rows from the prepared rows.
  Summary values, tables and calculations are unchanged. Single-variable banner
  raw values are retained; multidimensional bridges are unsupported and fail
  closed.
* web_canonical/identity_bridge.py defines a frozen, traceable mapping between
  canonical IDs and physical variable/raw codes. Duplicate identities and physical
  mappings fail validation. Supported scope is RU or column-per-option RM.
* canonical_materialization/legacy_bridge.py builds that mapping from released
  runtime bindings, without project, answer-text or brand rules.
* web_canonical/legacy_projection.py resolves physical metadata to an exact
  aggregate row, verifies configuration provenance and denominator, and extracts
  the actual Legacy metric. Display text is only a locator for the already
  established aggregate grain. Conflicting aggregates cannot be compared.
  Mention comparison requires the released PARENT_RM scope/ref.
* analytics_core/runner.py accepts the bridge only for projection, excluding it
  from Legacy execution arguments. Comparison records supplied through side
  channels remain non-authoritative.
* web_canonical/request_binding.py validates the materialization profile's
  explicit filter restriction and banner-only ordered coverage. Missing members,
  contradictory restrictions and unsupported request shapes fail closed.
* tests/test_gate19_corrective.py covers identity and binding positives and
  negatives; tests/test_gate19_benchmark_a.py covers the actual five productive
  requests, scope identity, repeated determinism and reconstructable provenance.
* scripts/validate_gate19_corrective.py reproduces execution using external
  source/package files, derives a Legacy datamap from released bindings, invokes
  the productive runner and retains complete comparison evidence. It does not
  introduce statistical calculations or classification overrides.

The execution adapter, accepted contracts, Benchmark package, default mode and
statistical methodology are unchanged. M6 integration files are modified;
materialization receives an additive bridge helper. These are integration
corrections, not analytical contract changes.

## VALIDATION

Before edits: repository remote, main branch, exact baseline SHA, clean worktree,
package SHA and runtime fingerprint were verified.

Package SHA-256:
`78AFA38484DC4B27FDD0AB5C3F8F2B80B2B49CABC67A57361B94BEB591685A41`.
Runtime Input fingerprint:
`eece0a4dec84266136033907b99b64b04d49428ff8c2d73846e4e36e910f5360`.

Focused corrective tests: 38 passed / 0 failed / 0 skipped.
Productive repeated run: BA-01 through BA-05 PASS, with respectively 40, 4, 4, 40
and 6 comparable records. All 94 records are exact PARITY. Representational,
contractual, unexpected numerical and unexpected structural differences: zero.
No tolerance or classification overrides were supplied. Determinism: PASS.
BA-03 retains MENTION / PARENT_RM / STR_Q_DELIVERY_APPS_RM_V1.

The successful probe evidence is
`_gate19_evidence/gate19_corrective_probe2_20260917.json`. Final committed-head
evidence is emitted separately as
`_gate19_evidence/gate19_corrective_validation_20260917.json`. It retains released
configuration, dataset/runtime/package identities, requests, universes/weights,
identity bridge, complete Canonical results, Legacy summaries/physical identities,
comparison keys, source refs, values and classifications. The first corrective
probe is also retained as history; its structure-reference validation error was
fixed before the successful rerun.

Dedicated Benchmark A tests: 8 passed / 0 failed / 0 skipped. Final full regression:
576 passed / 0 failed / 0 skipped. All required scopes were executed within that
full run; counts below are extracted from its JUnit report, not inferred from a
previous run. Pytest uses controlled external basetemp under
`C:/Users/conta/gate19_temp`, outside the git worktree. The initial full attempt
had 53 setup errors because the external basetemp parent did not exist. The parent
was created explicitly and the final run passed every test.

| Scope | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Gate 19 corrective | 38 | 0 | 0 |
| Canonical Materialization | 51 | 0 | 0 |
| Benchmark A productive | 8 | 0 | 0 |
| M2 universe evaluator modules | 31 | 0 | 0 |
| M3 weight runtime | 35 | 0 | 0 |
| M4 structure/mention and Legacy grid builders | 99 | 0 | 0 |
| M5 Canonical Results modules | 72 | 0 | 0 |
| M5 Execution Adapter | 44 | 0 | 0 |
| M6 modules | 97 | 0 | 0 |
| Legacy parity (wrapper + RM/grid) | 3 | 0 | 0 |
| Full repository regression | 576 | 0 | 0 |

The final JUnit report is
`C:/Users/conta/gate19_temp/gate19_full_regression_final.xml`. Additional contract
tests and unrelated accepted regression scopes are also covered by the full run.
The evidence importer records every JUnit classname with passed/failed/skipped
counts so these scope totals can be reconstructed.

No merge, default switch, M7 or productive Excel integration is authorized by this
review document.
