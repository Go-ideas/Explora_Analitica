# EXPLORA - M5 CANONICAL RESULTS REMEDIATION MANIFEST

**Milestone:** M5 - Canonical Results corrective remediation
**Date:** 2026-09-14
**Authority:** `M5_CANONICAL_RESULTS_IMPLEMENTATION_CONTRACT.md`
**Original failed checkpoint:** `checkpoints/M5_CANONICAL_RESULTS_2026-09-14.zip`
**Original failed checkpoint SHA-256:** `E4D8296B720992495D7964AB54DCB7A064B1F24B333185CCE2778CC9EC7BBC46`
**Runtime default:** `LEGACY`

## Corrected Blockers

- B-M5-IMPL-01 - RESULT FINGERPRINT / DETERMINISTIC ORDERING
- B-M5-IMPL-02 - NON-FINITE HANDLING + QA
- B-M5-IMPL-03 - UNKNOWN / UNSUPPORTED FORMULA QA + RELEASE
- B-M5-IMPL-04 - RELEASE MODEL / B3 CONSERVATIVE GATE

## Test Evidence

Pre-change:

- Full suite: 276 PASS / 0 FAIL / 0 SKIP
- Focused M5: 39 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP

Post-remediation:

- Focused M5: 63 PASS / 0 FAIL / 0 SKIP
- Full suite: 300 PASS / 0 FAIL / 0 SKIP
- Legacy parity: 2 PASS / 0 FAIL / 0 SKIP

## Files Modified

- `explora_web_reporter/src/analytics_core/results.py`
- `explora_web_reporter/src/analytics_core/formula_registry.py`
- `explora_web_reporter/src/analytics_core/serialization.py`
- `explora_web_reporter/src/analytics_core/result_identity.py`
- `explora_web_reporter/src/analytics_core/__init__.py`
- `explora_web_reporter/tests/test_canonical_results_identity.py`
- `explora_web_reporter/tests/test_canonical_results_serialization.py`
- `explora_web_reporter/tests/test_canonical_results_bases_values.py`
- `explora_web_reporter/tests/test_canonical_results_formulas.py`
- `explora_web_reporter/tests/test_canonical_results_significance_transport.py`
- `explora_web_reporter/tests/test_canonical_results_qa_release.py`
- `explora_web_reporter/tests/test_canonical_results_upstream_integration.py`

## Files Created

- `docs/explora_target/M5_CANONICAL_RESULTS_REMEDIATION.md`
- `docs/explora_target/M5_CANONICAL_RESULTS_REMEDIATION_MANIFEST.md`

## Contract Files Modified

NO

## M5 Source/Test Hashes

```text
17B7D6BE6DD9408AC1673F743D7BC34D174E7CA38949FE100A8217E256020B53  explora_web_reporter/src/analytics_core/results.py
00A617CBAA00D7B922870E8A34C9BC331C6721DBA352CD10D6DC6E4BC822B6DA  explora_web_reporter/src/analytics_core/formula_registry.py
14F21EAE83448FE3164F1000C8ED6E93F80945FE23354EB5421E525DD41E2F57  explora_web_reporter/src/analytics_core/serialization.py
B57CED04E2CDC02F848861EDC81E469F3733124D3712FBEA3886AC38C29F4AAB  explora_web_reporter/src/analytics_core/result_identity.py
5267C60011E1501DB3BC23481227DE22DCF025E5AA2FC2D564CF2A49B39469D6  explora_web_reporter/src/analytics_core/__init__.py
1D9AF3C84ADA22B06333EC32F3FF1604BEA847A44979C025910C67F3D3D70F49  explora_web_reporter/tests/test_canonical_results_identity.py
19362D9F13DAB6C54807461D3D593FB07BD20549CD970AA858416F3491AEC473  explora_web_reporter/tests/test_canonical_results_serialization.py
284D10020600F44AC6F036DC36A398E73BD8A12B1501676289FA11208304962A  explora_web_reporter/tests/test_canonical_results_bases_values.py
E1164AA9AA15B792EB5A0319416A3B8F1228AD554457EA8953CC9D979F731360  explora_web_reporter/tests/test_canonical_results_formulas.py
81F2D45540ADD6E59D9B7E25341FDB0232BE2C644DE86D0E353796FCFF38B6C2  explora_web_reporter/tests/test_canonical_results_significance_transport.py
BAF9595E5D72319F466FFD15F27C17F604D953FE580CF34502D4E8FA04CA02C2  explora_web_reporter/tests/test_canonical_results_qa_release.py
25FAC8AF0763F92734E44FAE12F7CCF1C4053412D2BA089B00B282B87C023732  explora_web_reporter/tests/test_canonical_results_upstream_integration.py
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

## Checkpoint

- File: `checkpoints/M5_CANONICAL_RESULTS_REMEDIATED_2026-09-14.zip`
- SHA-256: `EB30046FB4E49C8756A3B38DC18BA16B70BF11A32859570262F6E0ABB42179A3`

The packaged manifest records that the archive SHA is calculated after
packaging. The source manifest is updated after archive finalization with the
final checkpoint SHA-256, because embedding the archive hash inside the archive
would change the archive hash.

## Guardrails

- LEGACY remains default.
- M2 unchanged.
- M3 unchanged.
- M4 unchanged.
- Legacy productive source unchanged.
- Web/UI unchanged.
- SQLite unchanged.
- Excel not started.
- M6 not started.
- PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING
