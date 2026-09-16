# M4 Mention Scope Identity V1 Implementation Manifest

## Authority

- Gate: `26 - M4 Mention Scope Identity Implementation Authorization`
- Repository: `Go-ideas/Explora_Analitica`
- Base main SHA: `8d7781d3e46d4579a88d0cfdae48905774795874`
- Feature branch: `feature/m4-mention-scope-identity`

## Files Modified

Production source:

- `explora_web_reporter/src/contracts/vocabulary.py`
- `explora_web_reporter/src/contracts/models.py`
- `explora_web_reporter/src/contracts/validators.py`
- `explora_web_reporter/src/contracts/__init__.py`
- `explora_web_reporter/src/analytics_core/structure.py`
- `explora_web_reporter/src/analytics_core/execution_adapter.py`

Tests:

- `explora_web_reporter/tests/test_m4_mention_scope_identity.py`

Documentation:

- `docs/explora_target/M4_MENTION_SCOPE_IDENTITY_IMPLEMENTATION.md`
- `docs/explora_target/M4_MENTION_SCOPE_IDENTITY_IMPLEMENTATION_MANIFEST.md`

Unauthorized production source changes: `NO`

## SHA-256

- `18ac1b64fb273da39bea6bf2c035f46e078309629b6fca8cee21c879f3e3242e`  `explora_web_reporter/src/contracts/vocabulary.py`
- `87a386cd50a6bc109805739baa736bc50aeec69d47781efbce762ea4dcc61777`  `explora_web_reporter/src/contracts/models.py`
- `2604f9a0d093a8581b208c330ca6fd606de4bf23fb89fa17553ecbca8c3ca721`  `explora_web_reporter/src/contracts/validators.py`
- `a54b10edb65f8851bc0647e0d2468ecc5421877a51b833d1c9aaff2c9be54c12`  `explora_web_reporter/src/contracts/__init__.py`
- `99be9070d739338e189110841bdf124d324575cbdce727ff8190ea69b4c32986`  `explora_web_reporter/src/analytics_core/structure.py`
- `a11cea8d7984ea3007da7c49477ca15e29fda951607c15f6b91e4ffdc88ea986`  `explora_web_reporter/src/analytics_core/execution_adapter.py`
- `958f8b54acfcca0ed8c257b5b3cdf6041240d90da764d17fcfd704bb1b2e6bcd`  `explora_web_reporter/tests/test_m4_mention_scope_identity.py`

## Commands and Results

- `python -m pytest tests/test_m4_mention_scope_identity.py -q --basetemp "..._pytest_tmp_mscope_focus"`
  - Result: `29 PASS / 0 FAIL / 0 SKIP`
- `python -m pytest tests/test_structure_contract_extensions.py tests/test_structure_authority_corrective.py tests/test_structure_authority_runtime.py tests/test_m5_execution_adapter.py -q --basetemp "..._pytest_tmp_mscope_near"`
  - Result: `103 PASS / 0 FAIL / 0 SKIP`
- `python -m pytest tests/test_structure_authority_corrective.py tests/test_structure_authority_runtime.py tests/test_structure_contract_extensions.py tests/test_m4_mention_scope_identity.py -q --basetemp "..._pytest_tmp_mscope_m4"`
  - Result: `88 PASS / 0 FAIL / 0 SKIP`
- `python -m pytest tests/test_m5_execution_adapter.py -q --basetemp "..._pytest_tmp_mscope_m5_adapter"`
  - Result: `44 PASS / 0 FAIL / 0 SKIP`
- `python -m pytest tests/test_canonical_results_bases_values.py tests/test_canonical_results_formulas.py tests/test_canonical_results_identity.py tests/test_canonical_results_legacy_comparison.py tests/test_canonical_results_qa_release.py tests/test_canonical_results_serialization.py tests/test_canonical_results_significance_transport.py tests/test_canonical_results_upstream_integration.py tests/test_m5_execution_adapter.py -q --basetemp "..._pytest_tmp_mscope_m5"`
  - Result: `116 PASS / 0 FAIL / 0 SKIP`
- `python -m pytest <all tests/test_m6_*.py> -q --basetemp "..._pytest_tmp_mscope_m6"`
  - Result: `97 PASS / 0 FAIL / 0 SKIP`
- `python -m pytest tests/test_core_wrapper_parity.py tests/test_rm_grid_legacy_parity.py -q --basetemp "..._pytest_tmp_mscope_legacy"`
  - Result: `3 PASS / 0 FAIL / 0 SKIP`
- `python -m pytest --basetemp "..._pytest_tmp_mscope_full"`
  - Result: `479 PASS / 0 FAIL / 0 SKIP`

## MSCOPE Coverage

- MSCOPE-001: PASS
- MSCOPE-002: PASS
- MSCOPE-003: PASS
- MSCOPE-004: PASS
- MSCOPE-005: PASS
- MSCOPE-006: PASS
- MSCOPE-007: PASS
- MSCOPE-008: PASS
- MSCOPE-009: PASS
- MSCOPE-010: PASS
- MSCOPE-011: PASS
- MSCOPE-012: PASS
- MSCOPE-013: PASS
- MSCOPE-014: PASS
- MSCOPE-015: PASS
- MSCOPE-016: PASS
- MSCOPE-017: PASS
- MSCOPE-018: PASS
- MSCOPE-019: PASS
- MSCOPE-020: PASS
- MSCOPE-021: PASS
- MSCOPE-022: PASS
- MSCOPE-023: PASS
- MSCOPE-024: PASS
- MSCOPE-025: PASS
- MSCOPE-026: PASS
- MSCOPE-027: PASS
- MSCOPE-028: PASS

## Known Warnings

- Git line-ending warnings: LF may be replaced by CRLF on future Git touches in this Windows worktree.
- No GitHub CI checks are configured by this task.
- Benchmark A corrective release is not part of this implementation.
- Canonical Materialization remains stopped.
- Gate 19 remains blocked.
- Productive DUAL_RUN is not authorized.
- Default switch is not ready.
- M7 is not authorized.

## Blockers

None.

## Gate 27 Test-Only Corrective Remediation

Review result addressed: `FAIL - TEST EVIDENCE NONCONFORMANT`.

No productive code defect was identified. No productive source file was
modified in this corrective pass.

Corrected evidence:

- B-M4-MSI-TEST-01 / MSCOPE-018 now uses two distinct bindings/events with
  the same respondent, same option, and same row identity. Under
  `duplicate_policy=KEEP`, respondent contribution remains deduplicated while
  mention count preserves both duplicate mention events. The same fixture
  contrasts against `DEDUPLICATE_BY_CATEGORY` and `ERROR`.
- B-M4-MSI-TEST-02 / MSCOPE-025 now uses zero observed analytical records and
  a row ID declared only by `VariableBinding.row_id`, with no ROW axis. The
  declared binding row ID resolves successfully from the RELEASED
  `StructureSpec`; an undeclared row ID still fails closed.

Corrective focused result:

- `python -m pytest tests/test_m4_mention_scope_identity.py -q --basetemp "..._pytest_tmp_mscope_corrective_focus"`
  - Result: `29 PASS / 0 FAIL / 0 SKIP`

## Gate 27 Final Corrective Validation

B-M4-MSI-PROV-01 resolved: the manifest SHA-256 for
`explora_web_reporter/tests/test_m4_mention_scope_identity.py` now matches the
current PR head artifact exactly.

Current test artifact SHA-256:

- `958f8b54acfcca0ed8c257b5b3cdf6041240d90da764d17fcfd704bb1b2e6bcd`  `explora_web_reporter/tests/test_m4_mention_scope_identity.py`

Validation evidence:

- Focused MSCOPE: `29 PASS / 0 FAIL / 0 SKIP`
- Full regression: `479 PASS / 0 FAIL / 0 SKIP`
- Legacy parity: `3 PASS / 0 FAIL / 0 SKIP`

Confirmations:

- Productive source modified after `36e59eee497852159d0219b3c4ea92b476c7a2ce`: `NO`
- B-M4-MSI-TEST-01 remains resolved: MSCOPE-018 materially exercises true duplicate analytical identity and discriminates `KEEP`, `DEDUPLICATE_BY_CATEGORY`, and `ERROR`.
- B-M4-MSI-TEST-02 remains resolved: MSCOPE-025 materially exercises zero observed records, row identity declared only through `VariableBinding.row_id`, successful RELEASED `StructureSpec` resolution, and undeclared identity fail-closed.
- B-M4-MSI-PROV-01 resolved: manifest hash reconciled to the current test artifact.

Warnings:

- Git line-ending warnings may appear on Windows worktrees.
- GitHub CI is not configured by this task.
- The exact `python -m pytest` command encountered a local Windows
  `%TEMP%\pytest-of-conta` permission error during `tmp_path` setup for the
  database validation tests. A controlled rerun using an external
  `--basetemp` completed with `479 PASS / 0 FAIL / 0 SKIP`.
