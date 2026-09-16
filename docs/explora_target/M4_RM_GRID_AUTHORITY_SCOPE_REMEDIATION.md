# EXPLORA - M4 RM / GRID AUTHORITY SCOPE REMEDIATION

**Milestone:** M4 - RM / GRID AUTHORITY
**Corrective pass:** B-M4-IMPL-02R - Mention denominator scope execution
**Date:** 2026-09-14
**Authority:** `M4_RM_GRID_AUTHORITY_IMPLEMENTATION_CONTRACT.md`
**Runtime default:** `LEGACY` / `legacy_inference`

## Status

B-M4-IMPL-02R is remediated inside M4 Analytics Core structure runtime.
M5 was not started.

## Root Cause

The M4 runtime emitted a distinct mention ledger, but
`StructureSpec.mention_denominator_scope` was used only as traceability
metadata. It did not determine which valid mention events entered the mention
denominator.

This allowed a GRID_RM scope such as `row:row1` to include valid mentions from
other rows.

## Scope Execution Design

Mention denominator execution now applies scope membership after structural
normalization and before duplicate policy is applied to mention events.

Supported scope forms:

- `structure`
- `parent_structure`
- `all_options`
- `row`
- `row:<row_id>`
- `entity`
- `row/entity`
- `entity:<entity_id>`
- `loop_instance`
- `loop_instance:<loop_instance_id>`

Scope IDs are resolved only from stable released analytical identifiers:

- `row_id`
- `entity_id`
- `loop_instance_id`

No label matching, substring matching, case-insensitive guessing, variable-name
suffix inference, or fuzzy matching is used.

## Grid Tests

Added Grid scope tests cover:

- GRID_RM `row:row1` includes row1 mentions only;
- GRID_RM `row:row2` is independent;
- generic `row` emits independent row mention ledgers;
- duplicate KEEP operates inside row mention scope;
- the same option across row1 and row2 does not merge mention scopes;
- changing mention scope does not change the respondent ledger.

## Loop Tests

Added Loop scope tests cover:

- LOOP_RM `loop_instance:l1` includes only l1 mentions;
- generic `loop_instance` emits independent ledgers for l1 and l2;
- entity scope emits independent ledgers for different entities.

## Zero-Base Behavior

If a declared mention scope contains zero valid mentions, M4 returns a mention
ledger with:

- `denominator_n = 0`
- `zero_base_status = VALID_ZERO_BASE`

M4 does not borrow mentions from another row/entity/loop instance to avoid a
zero mention base.

## Invalid Scope Behavior

If `mention_denominator_scope` references an unknown row/entity/loop instance
or an unsupported scope form, M4 returns structured failure/review behavior and
does not fall back to full-structure mentions.

## Respondent Ledger Invariance

Mention-scope filtering affects only mention ledgers. The respondent ledger
continues to use unique analytical respondent-option identity with valid
SELECTED / NOT_SELECTED states.

## Test Evidence

Pre-change full baseline:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m4_scope_pre
```

Result: 226 PASS / 0 FAIL / 0 SKIP

Pre-change focused M4:

```powershell
python -m pytest -q tests\test_structure_contract_extensions.py tests\test_structure_authority_runtime.py tests\test_structure_authority_corrective.py tests\test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_m4_scope_pre_focus
```

Result: 50 PASS / 0 FAIL / 0 SKIP

Pre-change legacy parity:

```powershell
python -m pytest -q tests\test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_m4_scope_pre_parity
```

Result: 2 PASS / 0 FAIL / 0 SKIP

Focused M4 scope remediation:

```powershell
python -m pytest -q tests\test_structure_contract_extensions.py tests\test_structure_authority_runtime.py tests\test_structure_authority_corrective.py tests\test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_m4_scope_focus
```

Result: 61 PASS / 0 FAIL / 0 SKIP

Full regression:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m4_scope_full
```

Result: 237 PASS / 0 FAIL / 0 SKIP

Legacy parity:

```powershell
python -m pytest -q tests\test_rm_grid_legacy_parity.py --basetemp .pytest_tmp_m4_scope_parity
```

Result: 2 PASS / 0 FAIL / 0 SKIP

## Changed Artifacts

```text
CA9ED1A6BB951C1130AED2B1324DEBBDA862FD1DE74AE087975534B6D5AFEB56  .\explora_web_reporter\src\analytics_core\structure.py
8D9E1E055E159E80100DA904C82A5617AFC860DF3D75EFB7BCEE769DED528C6D  .\explora_web_reporter\tests\test_structure_authority_corrective.py
```

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

## Checkpoint

File: `checkpoints/M4_RM_GRID_AUTHORITY_SCOPE_REMEDIATED_2026-09-14.zip`

SHA-256:
`B4FD917329EF63565FA9A9EDFEB68BBA8FE5F0BA5B80EA8B08C67F993DF27C5B`

## Productive Grid / Loop Benchmark

PRODUCTIVE GRID/LOOP BENCHMARK = PENDING - HUMAN ACCEPTED WARNING

No actual traced real Grid/Loop benchmark was executed during this targeted
scope remediation. Synthetic/unit fixtures are not claimed as a productive
benchmark.

## Guardrails

- M2 Universe runtime was not modified.
- M3 Weight runtime was not modified.
- Productive Legacy behavior was not modified.
- Protected reporter files were not modified.
- Legacy RM/Grid/Scale builders were not modified.
- Grid loop detector behavior was not modified.
- Web/UI was not modified.
- SQLite/database behavior was not modified.
- Excel/VBA was not modified.
- NG was not modified.
- Significance runtime was not modified.
- No dependencies changed.
- No M5 work was started.
