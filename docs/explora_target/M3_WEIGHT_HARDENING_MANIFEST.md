# EXPLORA - M3 WEIGHT HARDENING MANIFEST

**Checkpoint date:** 2026-09-14
**Source root:** `C:\Users\conta\Go ideas\Local Go ideas - Documentos\Desarrollo\Explora Analitica`
**Working tree:** `explora_web_reporter`
**Git status:** no Git repository found in this workspace or parent directories. No repository was initialized.
**Checkpoint type:** SHA-256 file manifest plus archive checkpoint.

## Test Evidence

Pre-change baseline:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m3_impl_pre
```

Result: `141 passed`, `0 failed`, `0 skipped`.

Focused M3:

```powershell
python -m pytest -q tests\test_weight_runtime.py --basetemp .pytest_tmp_m3_focus_only
```

Result: `31 passed`, `0 failed`, `0 skipped`.

Focused M3 plus renderer/mode checks:

```powershell
python -m pytest -q tests\test_weight_runtime.py tests\test_contract_renderer_neutrality.py tests\test_core_execution_mode.py --basetemp .pytest_tmp_m3_focus
```

Result: `36 passed`, `0 failed`, `0 skipped`.

Full regression:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m3_full
```

Result: `172 passed`, `0 failed`, `0 skipped`.

Legacy vs CORE_WRAPPER parity:

```powershell
python -m pytest -q tests\test_core_wrapper_parity.py --basetemp .pytest_tmp_m3_parity
```

Result: `1 passed`, `0 failed`, `0 skipped`.

Productive legacy numerical deltas: none.

## Files Created

```text
1cecbd85b6bc5c036a2fb9a3fde2b9b1147f4f27eb6a0b49f68afec8e5737014  explora_web_reporter/src/analytics_core/weights.py
948e9840bf0bab28164f8ba85dfc2e38cbcf9a682d4acf25e8a7f46564792df4  explora_web_reporter/tests/test_weight_runtime.py
```

This document and `M3_WEIGHT_HARDENING.md` are hashed after creation and
reported in the final M3 response.

## Files Modified

```text
874904bcf37a02530dc4f6396bd9070fa03055f9ee2e4d88c1b08f1cb2537a13  explora_web_reporter/src/analytics_core/__init__.py
f290fbbcb5e9f7afd2ed7444cc5237f5345c7148b3d1208ed37476441be7a194  explora_web_reporter/tests/test_contract_renderer_neutrality.py
```

## Protected Hashes Confirmed

```text
d08612db5efb9349db7cef5b1b7a352398167f462b1db0868ed8ce20b263f83e  explora_web_reporter/src/analytics_core/universe.py
5867e952fe1378f76fe46efc4b0912cffa2154dd87a44c45fd8a0667e1da5fdb  explora_web_reporter/src/contracts/models.py
6c8bb25099ad262e0a32975ff291faf45e39f0fbd59bfab78b949c77f0ad7b40  explora_web_reporter/src/contracts/validators.py
a04687b44c7eec15aa6de3f05dab1a23e12f3c886a4eb8967b8ec960386498af  explora_web_reporter/src/contracts/vocabulary.py
1c49046db3387d1161a6ffebedbf5d2f92061f79442f9b97959c2f64f3a05c10  explora_web_reporter/src/reporter/calculations.py
a450e331001417855b296709771e35ce82df39806f62e1da67d107608bddc740  explora_web_reporter/src/reporter/tabulator.py
8e16036dc95912997b6661a79d0be0faa70843a0ab14bc79fb1efa3cac512fa6  explora_web_reporter/src/reporter/multi_metrics.py
33cc670c49838f41ebf3dc190eff7fd342cf641cada8ec03ec6ab94c0603c007  explora_web_reporter/src/reporter/significance.py
1f654641dd4e33fb054f1b72551849b65d78f15e4b2e9a75e3a395a0e2d6b223  explora_web_reporter/src/reporter/filters.py
2190bdf975d5dc59c24809b0547ca31a8f76d9255ecd24839fa1685f05fc945d  explora_web_reporter/src/reporter/banners.py
```

## Runtime Boundary

- Execution default: `LEGACY`.
- Existing feature flag: `EXPLORA_ANALYTICS_ENGINE`.
- No new dependency or production flag was added.
- M3 weight runtime is internal to Analytics Core and is not wired into the
  production Streamlit reporter path.

## Checkpoint Contents

The M3 checkpoint includes canonical target docs, M1A/M2/M3 docs, M3 contract,
`explora_web_reporter/src`, `explora_web_reporter/tests`, and app/requirements
files needed to reproduce the M3 and full regression tests where practical.

Excluded:

- datasets;
- SQLite/database outputs;
- secrets/env;
- logs;
- `__pycache__`;
- `.pyc`;
- pytest temp directories.

## Guardrails

No changes were made to:

- frozen contracts;
- M2 Universe implementation;
- productive legacy reporter files;
- runtime significance;
- Web/UI;
- SQLite/database behavior;
- Excel/VBA;
- NG;
- RM/Grid migration.

M4 was not started.
