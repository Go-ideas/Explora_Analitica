# T0 BASELINE VERIFICATION

Date: 2026-09-16

## Verification Summary

| Requirement | Status | Evidence |
| --- | --- | --- |
| GitHub `main` preserved | PASS | T0 work performed only on `migration/t0-canonical-baseline`. |
| Target PR branch inspected | PASS | PR #1 head was `80cd6032c4d8a29d54c4dcd870f484c745ee92ec`. |
| Physical project root identified | PASS | `explora_web_reporter/` under the workspace root. |
| Physical root Git status | NOT FOUND | Workspace root was not a Git repository. |
| Python runtime identified | PASS | Python `3.13.3`. |
| Dependencies identified | PASS | `explora_web_reporter/requirements.txt`. |
| Checkpoint SHA verification | PASS | M5 adapter corrective checkpoint SHA matches `B273D859FB29FA01129B8DE622646A197D48472DCB3B0E568E42AFFD15A81159`. |
| Source/checkpoint reconciliation | AMBIGUOUS | No single checkpoint exactly represents the full current physical tree; M6 V3 sampled files match current source, M5 adapter checkpoint hash matches historical evidence. |
| B1 policy preserved | PASS | No methodology edits during T0. |
| B2 policy preserved | PASS | No methodology edits during T0. |
| B3 policy preserved | PASS | No methodology edits during T0. |
| LEGACY default preserved | PASS | `resolve_execution_mode(None)` defaults to `ExecutionMode.LEGACY`; UI defaults to `LEGACY` absent explicit selection. |
| CANONICAL_V1 explicit only | PASS | Requires explicit mode and explicit `CanonicalResult`. |
| DUAL_RUN explicit only | PASS | Requires explicit mode. |
| Materialization source present | NOT FOUND | `src/canonical_materialization/` absent in physical tree. |
| Client data excluded | PASS | SAV/DB/data/output/evidence/checkpoints excluded from adopted Git payload. |
| Full regression on physical tree | PASS | `450 passed / 0 failed / 0 skipped`. |
| Full regression on adopted Git payload without client DB | FAIL | `1 failed, 449 passed`; missing excluded `data/db/BD_Analitica_Explora.db`. |

## Test Baseline

Commands executed from `explora_web_reporter/` with `PYTHONPATH=.`:

| Suite | Result |
| --- | --- |
| M2 Universe | `31 passed / 0 failed / 0 skipped` |
| M3 Weight | `45 passed / 0 failed / 0 skipped` |
| M4 Structure / RM Grid | `61 passed / 0 failed / 0 skipped` |
| M5 Canonical Results | `75 passed / 0 failed / 0 skipped` |
| M5 Execution Adapter | `44 passed / 0 failed / 0 skipped` |
| M6 Web Canonical | `97 passed / 0 failed / 0 skipped` |
| Legacy parity | `2 passed / 0 failed / 0 skipped` |
| Materialization | `NOT FOUND` |
| Full regression, physical tree | `450 passed / 0 failed / 0 skipped` |
| Full regression, adopted Git payload | `1 failed / 449 passed / 0 skipped` |

## Protected Source Hashes

| File | SHA-256 |
| --- | --- |
| `explora_web_reporter/src/analytics_core/universe.py` | `D08612DB5EFB9349DB7CEF5B1B7A352398167F462B1DB0868ED8CE20B263F83E` |
| `explora_web_reporter/src/analytics_core/weights.py` | `AC6AA9C51A4AC32ED5329C689DA93D1572D2FA55A271EE424E082499AEB3472B` |
| `explora_web_reporter/src/analytics_core/structure.py` | `CA9ED1A6BB951C1130AED2B1324DEBBDA862FD1DE74AE087975534B6D5AFEB56` |
| `explora_web_reporter/src/analytics_core/results.py` | `17B7D6BE6DD9408AC1673F743D7BC34D174E7CA38949FE100A8217E256020B53` |
| `explora_web_reporter/src/analytics_core/result_identity.py` | `1925B1B8892D293838FD3A396A32499BCAF5F628B66464B0BD81A1C4D3B43696` |
| `explora_web_reporter/src/analytics_core/serialization.py` | `DC750044B8D0008C5848AB7E73ACE309C579174089827104E7A7E900F179865B` |
| `explora_web_reporter/src/analytics_core/formula_registry.py` | `00A617CBAA00D7B922870E8A34C9BC331C6721DBA352CD10D6DC6E4BC822B6DA` |
| `explora_web_reporter/src/analytics_core/execution_adapter.py` | `3EA9C89565573BC9C92A0F9365762306CC942C3D4AB54BC54AC558A2D5A78B41` |
| `explora_web_reporter/src/reporter/tabulator.py` | `A450E331001417855B296709771E35CE82DF39806F62E1DA67D107608BDDC740` |
| `explora_web_reporter/src/reporter/calculations.py` | `1C49046DB3387D1161A6FFEBEDBF5D2F92061F79442F9B97959C2F64F3A05C10` |
| `explora_web_reporter/src/reporter/filters.py` | `1F654641DD4E33FB054F1B72551849B65D78F15E4B2E9A75E3A395A0E2D6B223` |
| `explora_web_reporter/src/reporter/banners.py` | `2190BDF975D5DC59C24809B0547CA31A8F76D9255ECD24839FA1685F05FC945D` |
| `explora_web_reporter/src/reporter/significance.py` | `33CC670C49838F41EBF3DC190EFF7FD342CF641CADA8EC03EC6AB94C0603C007` |

## Numerical Deltas

Productive Legacy numerical deltas were not executed during T0. Legacy parity regression passed.

## Warnings

- No single authoritative checkpoint ZIP exactly represents the complete current physical source tree.
- Canonical materialization package/tests are not present in the inspected physical tree.
- Clean-clone/adopted-payload reproducibility fails because `tests/test_database_validation.py` depends on `data/db/BD_Analitica_Explora.db`, a 17,551,360-byte SQLite file that is prohibited from GitHub upload under T0 data rules.
