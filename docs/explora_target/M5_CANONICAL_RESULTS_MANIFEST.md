# EXPLORA - M5 CANONICAL RESULTS MANIFEST

**Milestone:** M5 - Canonical Results
**Date:** 2026-09-14
**Authority:** `M5_CANONICAL_RESULTS_IMPLEMENTATION_CONTRACT.md`
**Authority SHA-256:** `A36D8803F84357868C450956A33D8D66B432E1C473494C9C9BE9BE2CF618431D`
**Runtime default:** `LEGACY`
**Repository mode:** no Git repository detected; checkpoint uses SHA-256 file
hashes.

## Test Evidence

Pre-change baseline:

- Command: `python -m pytest -q --basetemp .pytest_tmp_m5_pre`
- Result: 237 PASS / 0 FAIL / 0 SKIP

Pre-change Legacy parity:

- Command: `python -m pytest -q tests/test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_m5_pre_parity`
- Result: 2 PASS / 0 FAIL / 0 SKIP

Focused M5:

- Command: `python -m pytest -q tests/test_canonical_results_identity.py tests/test_canonical_results_serialization.py tests/test_canonical_results_bases_values.py tests/test_canonical_results_formulas.py tests/test_canonical_results_significance_transport.py tests/test_canonical_results_qa_release.py tests/test_canonical_results_legacy_comparison.py tests/test_canonical_results_upstream_integration.py --basetemp .pytest_tmp_m5_focused`
- Result: 39 PASS / 0 FAIL / 0 SKIP

Full regression:

- Command: `python -m pytest -q --basetemp .pytest_tmp_m5_full`
- Result: 276 PASS / 0 FAIL / 0 SKIP

Final Legacy parity:

- Command: `python -m pytest -q tests/test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_m5_final_parity`
- Result: 2 PASS / 0 FAIL / 0 SKIP

## Files Created

- `explora_web_reporter/src/analytics_core/results.py`
- `explora_web_reporter/src/analytics_core/formula_registry.py`
- `explora_web_reporter/src/analytics_core/serialization.py`
- `explora_web_reporter/src/analytics_core/result_identity.py`
- `explora_web_reporter/tests/test_canonical_results_identity.py`
- `explora_web_reporter/tests/test_canonical_results_serialization.py`
- `explora_web_reporter/tests/test_canonical_results_bases_values.py`
- `explora_web_reporter/tests/test_canonical_results_formulas.py`
- `explora_web_reporter/tests/test_canonical_results_significance_transport.py`
- `explora_web_reporter/tests/test_canonical_results_qa_release.py`
- `explora_web_reporter/tests/test_canonical_results_legacy_comparison.py`
- `explora_web_reporter/tests/test_canonical_results_upstream_integration.py`
- `docs/explora_target/M5_CANONICAL_RESULTS_IMPLEMENTATION.md`
- `docs/explora_target/M5_CANONICAL_RESULTS_MANIFEST.md`

## Files Modified

- `explora_web_reporter/src/contracts/vocabulary.py`
- `explora_web_reporter/src/contracts/models.py`
- `explora_web_reporter/src/contracts/validators.py`
- `explora_web_reporter/src/contracts/__init__.py`
- `explora_web_reporter/src/analytics_core/__init__.py`

## Contract Extensions

All M5 contract extensions are additive and backward compatible. No frozen
pre-existing field semantics were changed.

Added vocabulary:

- `ValueStatus`
- `ValueUnit`
- `ComputationStatus`
- `QAReleaseStatus`
- `QADomain`
- `QAScopeType`
- `LegacyCanonicalComparisonStatus`

Added models:

- `CanonicalResultManifest`
- `RequestSnapshot`
- `CanonicalSlice`
- `CanonicalBase`
- `CanonicalValue`
- `SignificanceRelation`
- `QAEvent`
- `CanonicalReleaseState`
- `FormulaRegistryEntry`
- `LegacyCanonicalComparison`

Extended model:

- `CanonicalResult` gained optional/defaulted M5 typed collections and metadata.
  Existing required fields and legacy skeleton collections remain compatible.

## Source Hashes

```text
987DA010BF6B48DC45F6840F018A1D97A1EB541D2D341A9F8A3A95D4EC2F85C1  explora_web_reporter/src/analytics_core/results.py
70543BB7BB19C1EA6ECB3700127D8D1FCCDD99A90E7482BFD87EDB89DD3D7D5E  explora_web_reporter/src/analytics_core/formula_registry.py
3E445A53135DB1986D64D09D0D37D8119D1EDB8055127F5C0CB1526B29523DAE  explora_web_reporter/src/analytics_core/serialization.py
AEA65D348AE52CE9EB6593A2F8AAC52CDE8627C5C21AF6FE5D78E760FF019AEC  explora_web_reporter/src/analytics_core/result_identity.py
ACD20711D9CD9996C9FBBD52D4AD50A54FE5493292879F876F7D3F6D2668416F  explora_web_reporter/src/contracts/models.py
C95F9D2BAB7C8979DBE7547CF77DC15CA51A2AA58F93BF34971FC26528B3C66F  explora_web_reporter/src/contracts/vocabulary.py
999034BA396C5AE4BBB09BCBCB86360300F568416E941A21867C54C7076C5A37  explora_web_reporter/src/contracts/validators.py
8162E694A3E1CCDE2289EE358BF937BE6BAE5581039C31E1A1D47C8574A289CD  explora_web_reporter/src/contracts/__init__.py
62CA7805B510A8EB9EFCB3A2EE81C902EF724792913C4AD504C12A54AD8C7EB1  explora_web_reporter/src/analytics_core/__init__.py
```

## Protected Hash Evidence

```text
D08612DB5EFB9349DB7CEF5B1B7A352398167F462B1DB0868ED8CE20B263F83E  explora_web_reporter/src/analytics_core/universe.py
AC6AA9C51A4AC32ED5329C689DA93D1572D2FA55A271EE424E082499AEB3472B  explora_web_reporter/src/analytics_core/weights.py
CA9ED1A6BB951C1130AED2B1324DEBBDA862FD1DE74AE087975534B6D5AFEB56  explora_web_reporter/src/analytics_core/structure.py
A450E331001417855B296709771E35CE82DF39806F62E1DA67D107608BDDC740  explora_web_reporter/src/reporter/tabulator.py
1C49046DB3387D1161A6FFEBEDBF5D2F92061F79442F9B97959C2F64F3A05C10  explora_web_reporter/src/reporter/calculations.py
1F654641DD4E33FB054F1B72551849B65D78F15E4B2E9A75E3A395A0E2D6B223  explora_web_reporter/src/reporter/filters.py
2190BDF975D5DC59C24809B0547CA31A8F76D9255ECD24839FA1685F05FC945D  explora_web_reporter/src/reporter/banners.py
33CC670C49838F41EBF3DC190EFF7FD342CF641CADA8EC03EC6AB94C0603C007  explora_web_reporter/src/reporter/significance.py
1662F10AED0488A09485A06E5DEA70146A2C9E62615668145C9D88B0178140D4  explora_web_reporter/src/structure/grid_loop_detector.py
CBA017B2A40C1A8F038287175EC99955F1A8E686AC8AC9F4CB058310C2CD83BD  explora_web_reporter/src/builder/rm_long_builder.py
13A6638F8FB642BCCC5CD25DBE8D4405494EB29D758E19ECDB695ACD4BD99678  explora_web_reporter/src/builder/grid_loop_long_builder.py
211C2179228CBDF285131C9F5493629F62D8E8F390902BD710A525A1ADCF327C  explora_web_reporter/src/builder/escalas_long_builder.py
```

## Guardrails

- LEGACY remains default.
- M2 files were not modified.
- M3 files were not modified.
- M4 files were not modified.
- Legacy productive files were not modified.
- Web/UI unchanged.
- SQLite unchanged.
- Excel not started.
- M6 not started.

## Productive Grid / Loop Benchmark

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING

M5 does not convert this warning into productive validation.

## Checkpoint

- File: `checkpoints/M5_CANONICAL_RESULTS_2026-09-14.zip`
- SHA-256: `E4D8296B720992495D7964AB54DCB7A064B1F24B333185CCE2778CC9EC7BBC46`

The final checkpoint ZIP contains this manifest. The manifest SHA-256 and
checkpoint SHA-256 are reported in the final implementation response.

Because the archive contains this manifest, embedding the archive's own final
hash inside the packaged manifest would change the archive hash. The source
manifest is updated after archive finalization with the final checkpoint
SHA-256.
