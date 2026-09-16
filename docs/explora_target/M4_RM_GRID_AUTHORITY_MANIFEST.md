# EXPLORA - M4 RM / GRID AUTHORITY MANIFEST

**Milestone:** M4 - RM / GRID AUTHORITY
**Date:** 2026-09-14
**Authority:** `M4_RM_GRID_AUTHORITY_IMPLEMENTATION_CONTRACT.md`
**Runtime default:** `LEGACY` / `legacy_inference`
**Repository mode:** no Git repository detected; checkpoint uses SHA-256 file
hashes.

## Status

M4 implementation is complete and isolated.

## Checkpoint

- File: `checkpoints/M4_RM_GRID_AUTHORITY_2026-09-14.zip`
- SHA-256: `939076BEEF92ED6122B0AD16462A629A0E0D9655651E1CF41D9A10565879EF14`

The final archive SHA-256 is calculated after packaging. Because the archive
contains this manifest, embedding the archive's own final hash inside the
packaged manifest would change the archive hash. The source manifest is updated
after archive finalization with the final checkpoint SHA-256.

## Test Evidence

Pre-change baseline:

- Command: `python -m pytest -q --basetemp .pytest_tmp_m4_baseline`
- Result: 176 PASS / 0 FAIL / 0 SKIP

Focused M4:

- Command: `python -m pytest -q tests\test_structure_contract_extensions.py tests\test_structure_authority_runtime.py tests\test_rm_grid_legacy_parity.py`
- Result: 40 PASS / 0 FAIL / 0 SKIP

Full regression:

- Command: `python -m pytest -q --basetemp .pytest_tmp_m4_final`
- Result: 216 PASS / 0 FAIL / 0 SKIP
- Re-gate command: `python -m pytest -q --basetemp .pytest_tmp_m4_regate_full`
- Re-gate result: 216 PASS / 0 FAIL / 0 SKIP

Legacy parity:

- Command: `python -m pytest -q tests\test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_m4_parity`
- Result: 2 PASS / 0 FAIL / 0 SKIP
- Re-gate command: `python -m pytest -q tests\test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_m4_regate_parity`
- Re-gate result: 2 PASS / 0 FAIL / 0 SKIP

Focused M4 re-gate:

- Command: `python -m pytest -q tests\test_structure_contract_extensions.py tests\test_structure_authority_runtime.py tests\test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_m4_regate_focus`
- Result: 40 PASS / 0 FAIL / 0 SKIP

## Checkpoint Content

The final checkpoint includes:

- M4 implementation contract, implementation report and manifest;
- `explora_web_reporter/src/contracts/`;
- `explora_web_reporter/src/analytics_core/`;
- all `explora_web_reporter/tests/` Python tests for reproduction;
- protected legacy audit surfaces under `explora_web_reporter/src/reporter/`;
- RM/Grid/Scale legacy builders;
- `explora_web_reporter/src/structure/grid_loop_detector.py`;
- `explora_web_reporter/app.py`;
- `explora_web_reporter/streamlit_app.py`;
- `explora_web_reporter/requirements.txt`;
- `explora_web_reporter/README.md`;
- `.streamlit` configuration files when present and non-secret.

Excluded:

- client datasets;
- production SQLite outputs;
- secrets/env files;
- logs;
- `__pycache__`;
- `.pyc`;
- pytest temp directories.

## Changed Artifacts

```text
4642ACD134FDC256DC3585784CD57178A5BDB8CC3C3360FF46C5BFDC870EEFD8  .\docs\explora_target\M4_RM_GRID_AUTHORITY_IMPLEMENTATION_CONTRACT.md
05709B97FA5152D4C1074633EF67AFEA482697B8491A39CFB5A6686F1516D572  .\docs\explora_target\M4_RM_GRID_AUTHORITY.md
AD71CE5CC272C15F7548DDB6E041893BA6F676ABFC5D60549AE5B040B284CC4E  .\explora_web_reporter\src\contracts\vocabulary.py
D7C04D45E4559CD246F4AE510CA1AE184619655EB517948A2C0E6A23763C9FBA  .\explora_web_reporter\src\contracts\models.py
0A9F74368E0943AA691E5B8CF99D6EB23974CFD660436A6CFFACB8C635E8DD63  .\explora_web_reporter\src\contracts\validators.py
AA2E1D20FA5E36D2304D0DFDD3326A619486E2E51C5927EA336365972EE0CE92  .\explora_web_reporter\src\contracts\__init__.py
2530AA00913EF8E063D9D2E263744170B72A8CB26AAA85DD603393FB5B1ACB39  .\explora_web_reporter\src\analytics_core\structure.py
A828A8232FB5FD514900BE49D3AB47C6EE78D50D2A1F1E30A7E13CF4CA2888F9  .\explora_web_reporter\tests\test_structure_contract_extensions.py
E221B94CCC64CE917059698A368DC360584D11B7D8FDD5A96161C237296860C4  .\explora_web_reporter\tests\test_structure_authority_runtime.py
D7A7E3AF9A0BFB51F362A8069E4478946846DBB9768E2EAE2BCB10A7EC80E433  .\explora_web_reporter\tests\test_rm_grid_legacy_parity.py
```

## New Files

- `docs/explora_target/M4_RM_GRID_AUTHORITY.md`
- `docs/explora_target/M4_RM_GRID_AUTHORITY_MANIFEST.md`
- `explora_web_reporter/src/analytics_core/structure.py`
- `explora_web_reporter/tests/test_structure_contract_extensions.py`
- `explora_web_reporter/tests/test_structure_authority_runtime.py`
- `explora_web_reporter/tests/test_rm_grid_legacy_parity.py`

## Modified Files

- `explora_web_reporter/src/contracts/vocabulary.py`
- `explora_web_reporter/src/contracts/models.py`
- `explora_web_reporter/src/contracts/validators.py`
- `explora_web_reporter/src/contracts/__init__.py`

## Protected Files

The following protected surfaces were not modified:

- M2 Universe runtime files;
- M3 Weight runtime files;
- `src/reporter/tabulator.py`;
- `src/reporter/calculations.py`;
- `src/reporter/filters.py`;
- `src/reporter/banners.py`;
- `src/reporter/significance.py`;
- `src/structure/grid_loop_detector.py`;
- `rm_long_builder.py`;
- `grid_loop_long_builder.py`;
- `escalas_long_builder.py`;
- Web/UI;
- SQLite/persistence;
- Excel/VBA;
- NG.

## Protected Hash Evidence

```text
D08612DB5EFB9349DB7CEF5B1B7A352398167F462B1DB0868ED8CE20B263F83E  .\explora_web_reporter\src\analytics_core\universe.py
AC6AA9C51A4AC32ED5329C689DA93D1572D2FA55A271EE424E082499AEB3472B  .\explora_web_reporter\src\analytics_core\weights.py
A450E331001417855B296709771E35CE82DF39806F62E1DA67D107608BDDC740  .\explora_web_reporter\src\reporter\tabulator.py
1C49046DB3387D1161A6FFEBEDBF5D2F92061F79442F9B97959C2F64F3A05C10  .\explora_web_reporter\src\reporter\calculations.py
1F654641DD4E33FB054F1B72551849B65D78F15E4B2E9A75E3A395A0E2D6B223  .\explora_web_reporter\src\reporter\filters.py
2190BDF975D5DC59C24809B0547CA31A8F76D9255ECD24839FA1685F05FC945D  .\explora_web_reporter\src\reporter\banners.py
33CC670C49838F41EBF3DC190EFF7FD342CF641CADA8EC03EC6AB94C0603C007  .\explora_web_reporter\src\reporter\significance.py
1662F10AED0488A09485A06E5DEA70146A2C9E62615668145C9D88B0178140D4  .\explora_web_reporter\src\structure\grid_loop_detector.py
CBA017B2A40C1A8F038287175EC99955F1A8E686AC8AC9F4CB058310C2CD83BD  .\explora_web_reporter\src\builder\rm_long_builder.py
13A6638F8FB642BCCC5CD25DBE8D4405494EB29D758E19ECDB695ACD4BD99678  .\explora_web_reporter\src\builder\grid_loop_long_builder.py
211C2179228CBDF285131C9F5493629F62D8E8F390902BD710A525A1ADCF327C  .\explora_web_reporter\src\builder\escalas_long_builder.py
```

## Contract Extension Summary

| Model / field | Additive | Backward compatible | Existing frozen semantics changed |
| --- | --- | --- | --- |
| `StructureAuthorityMode` vocabulary | YES | YES | NO |
| `StructureType` vocabulary | YES | YES | NO |
| `AxisRole` vocabulary | YES | YES | NO |
| `StorageEncoding` vocabulary | YES | YES | NO |
| `ResponseStateValue` vocabulary | YES | YES | NO |
| `DuplicatePolicy` vocabulary | YES | YES | NO |
| `CompletionPolicy` vocabulary | YES | YES | NO |
| `DenominatorUnit` vocabulary | YES | YES | NO |
| `StructureExecutionStatus` vocabulary | YES | YES | NO |
| `LegacyStructureComparisonStatus` vocabulary | YES | YES | NO |
| `QuestionSpec.structure_ref` | YES | YES | NO |
| `QuestionSpec.category_refs` | YES | YES | NO |
| `StructureMember` model | YES | YES | NO |
| `StructureAxis` model | YES | YES | NO |
| `VariableBinding` model | YES | YES | NO |
| `CategoryOptionBinding` model | YES | YES | NO |
| `StructureSpec.axes` | YES | YES | NO |
| `StructureSpec.variable_bindings` | YES | YES | NO |
| `StructureSpec.category_bindings` | YES | YES | NO |
| `StructureSpec.applicability_refs` | YES | YES | NO |
| `StructureSpec.selected_values` | YES | YES | NO |
| `StructureSpec.not_selected_values` | YES | YES | NO |
| `StructureSpec.ordinary_missing_values` | YES | YES | NO |
| `StructureSpec.completion_policy` | YES | YES | NO |
| `StructureSpec.duplicate_policy` | YES | YES | NO |
| `StructureSpec.exclusive_option_ids` | YES | YES | NO |
| `StructureSpec.storage_encoding` | YES | YES | NO |
| `StructureSpec.loop_instance_binding` | YES | YES | NO |
| `StructureSpec.mention_denominator_scope` | YES | YES | NO |
| `StructureSpec.structural_zero_provenance` | YES | YES | NO |
| `StructureSpec.structural_missing_semantics` | YES | YES | NO |
| `StructureSpec.response_state_version` | YES | YES | NO |
| `validate_structure_spec(..., enforce_m4=False)` optional parameters | YES | YES | NO |

## Productive Grid / Loop Benchmark

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING

No actual traced real Grid/Loop benchmark was executed during M4 packaging.
Synthetic unit/integration tests are not counted as a productive benchmark.

## Known Warnings

- No Git repository was detected, so checkpoint evidence is SHA-256 based
  rather than commit based.
- Productive Grid/Loop benchmark is pending.
- The source manifest records the final checkpoint SHA-256 after archive
  finalization; the packaged copy necessarily precedes that final archive hash.

## Guardrail Confirmation

- LEGACY remains default.
- No runtime inference overrides RELEASED Specs.
- M2 files were not modified.
- M3 files were not modified.
- Web/SQLite/Excel/NG/significance remain untouched.
- M5 was not started.
