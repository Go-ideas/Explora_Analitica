# EXPLORA - M3 WEIGHT HARDENING REMEDIATION MANIFEST

**Checkpoint date:** 2026-09-14
**Source root:** `C:\Users\conta\Go ideas\Local Go ideas - Documentos\Desarrollo\Explora Analitica`
**Working tree:** `explora_web_reporter`
**Git status:** no Git repository found in this workspace or parent directories. No repository was initialized.
**Checkpoint type:** SHA-256 file manifest plus archive checkpoint.

## Corrective Scope

B-M3-01 remediates type-dependent NaN classification in the M3 Analytics Core
weight runtime.

Only the M3 runtime and M3 tests were changed. Remediation documentation and
this manifest were added.

## Test Evidence

Pre-change full baseline:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m3_nan_pre
```

Result: `172 passed`, `0 failed`, `0 skipped`.

Focused M3 remediation:

```powershell
python -m pytest -q tests\test_weight_runtime.py --basetemp .pytest_tmp_m3_nan_focus
```

Result: `35 passed`, `0 failed`, `0 skipped`.

Full regression:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m3_nan_full
```

Result: `176 passed`, `0 failed`, `0 skipped`.

Legacy vs CORE_WRAPPER parity:

```powershell
python -m pytest -q tests\test_core_wrapper_parity.py --basetemp .pytest_tmp_m3_nan_parity
```

Result: `1 passed`, `0 failed`, `0 skipped`.

Productive legacy numerical deltas: none.

## Files Modified

```text
ac6aa9c51a4ac32ed5329c689da93d1572d2fa55a271ee424e082499aeb3472b  explora_web_reporter/src/analytics_core/weights.py
b326a8340ffc67252052deca5a36880c86d41f4ae0d9f83e243cddad8cdd67f8  explora_web_reporter/tests/test_weight_runtime.py
```

## Files Created

```text
docs/explora_target/M3_WEIGHT_HARDENING_REMEDIATION.md
docs/explora_target/M3_WEIGHT_HARDENING_REMEDIATION_MANIFEST.md
checkpoints/M3_WEIGHT_HARDENING_REMEDIATED_2026-09-14.zip
```

The remediation documentation hashes and archive SHA-256 are reported after
checkpoint creation.

## Protected Hashes Confirmed

```text
5867e952fe1378f76fe46efc4b0912cffa2154dd87a44c45fd8a0667e1da5fdb  explora_web_reporter/src/contracts/models.py
d08612db5efb9349db7cef5b1b7a352398167f462b1db0868ed8ce20b263f83e  explora_web_reporter/src/analytics_core/universe.py
a450e331001417855b296709771e35ce82df39806f62e1da67d107608bddc740  explora_web_reporter/src/reporter/tabulator.py
1c49046db3387d1161a6ffebedbf5d2f92061f79442f9b97959c2f64f3a05c10  explora_web_reporter/src/reporter/calculations.py
1f654641dd4e33fb054f1b72551849b65d78f15e4b2e9a75e3a395a0e2d6b223  explora_web_reporter/src/reporter/filters.py
2190bdf975d5dc59c24809b0547ca31a8f76d9255ecd24839fa1685f05fc945d  explora_web_reporter/src/reporter/banners.py
33cc670c49838f41ebf3dc190eff7fd342cf641cada8ec03ec6ab94c0603c007  explora_web_reporter/src/reporter/significance.py
```

## Guardrails

- `LEGACY` remains default.
- B1 methodology is unchanged.
- Frozen contracts are unchanged.
- M2 Universe implementation is unchanged.
- M3 consumes the M2 mask and does not modify it.
- Missing / NaN never becomes weight `1`.
- Positive and negative infinity remain blocking.
- No normalization, trimming, capping, winsorization, imputation or rounding
  mutation was added.
- `weighted_n_raw == weighted_n` remains true in V1.
- Kish effective N remains QA only.
- Weighted significance remains `UNSUPPORTED` V1.
- No Web/SQLite/Excel/NG/RM/Grid migration occurred.
- M4 was not started.
