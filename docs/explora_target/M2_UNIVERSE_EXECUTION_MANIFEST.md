# EXPLORA — M2 UNIVERSE EXECUTION MANIFEST

**Checkpoint date:** 2026-09-14
**Source root:** `C:\Users\conta\Go ideas\Local Go ideas - Documentos\Desarrollo\Explora Analitica`
**Working tree:** `explora_web_reporter`
**Git status:** no Git repository found in this workspace or parent directories. No repository was initialized.
**Checkpoint type:** SHA-256 file manifest plus archive checkpoint.

## Test Evidence

Baseline before M2:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m2_preflight
```

Result: `110 passed`, `0 failed`, `0 skipped`.

M2 final full suite:

```powershell
python -m pytest -q --basetemp .pytest_tmp_m2_full_final
```

Result: `129 passed`, `0 failed`, `0 skipped`.

M2 final focused suite:

```powershell
python -m pytest -q tests -k "universe_evaluator or renderer_neutrality" --basetemp .pytest_tmp_m2_new2
```

Result: `21 passed`, `108 deselected`.

## Runtime Boundary

- Execution default: `LEGACY`.
- Feature flag: `EXPLORA_ANALYTICS_ENGINE`.
- M2 Universe evaluator is not wired into production Web/reporting runtime.
- Runtime weights/significance/RM/Grid/Excel/NG remain untouched.

## Included Files

This manifest covers the M2 implementation files, M2 tests, frozen M1A
contract/core surface, and canonical target documents. Generated caches, pytest
temp directories, datasets and SQLite outputs are excluded.

```text
41a6f80d336068fd083bbeb3266baaf08d091d9a689f97cdce77daccb4f436c9  explora_web_reporter/src/contracts/__init__.py
a04687b44c7eec15aa6de3f05dab1a23e12f3c886a4eb8967b8ec960386498af  explora_web_reporter/src/contracts/vocabulary.py
5867e952fe1378f76fe46efc4b0912cffa2154dd87a44c45fd8a0667e1da5fdb  explora_web_reporter/src/contracts/models.py
6c8bb25099ad262e0a32975ff291faf45e39f0fbd59bfab78b949c77f0ad7b40  explora_web_reporter/src/contracts/validators.py
0bf861e43e8fab49c4a4254a56f6d4d4c763415dad99a940c0038a6051ba777a  explora_web_reporter/src/analytics_core/__init__.py
25d77c319a9ccf3c0927ff34928ac8b658155f131535baf8a51c36ace7959ad6  explora_web_reporter/src/analytics_core/mode.py
57b30e2eb4e5f503b488653ba76bd9453da7707cc9e09544e8a637a3b337ef06  explora_web_reporter/src/analytics_core/interface.py
30a3b302003b753457cf347a08fe9f2b57b2fdeea8e0d0a80e7d896ca6afbb36  explora_web_reporter/src/analytics_core/legacy_adapter.py
4ac8f7640fda87570e9ce937e6626d6e3449733b3400067246f53adf2aeeda5f  explora_web_reporter/src/analytics_core/runner.py
01e9edcd8d7a1df0a6519854f32a6bef176a87606079cdbe418f3be1efd7dee1  explora_web_reporter/src/analytics_core/universe.py
297f32271a2d9f2f3951b7b323258d5ebbe9e96ab255ac50d4c8d0dbd1ff3a5e  explora_web_reporter/tests/test_contract_vocabularies.py
65daa9f51520610ed58ef3431b69e44c0243a0401ad73f3429516a8684dbd480  explora_web_reporter/tests/test_contract_ai_release_guard.py
d87d5c494adbeac339a3a5dc15535a15698255ab292b94316be66240497c7f80  explora_web_reporter/tests/test_contract_weight_policy.py
657b736fd620c4131001cd4892da28c21aff678f80c4c84fae14155278c5b9ef  explora_web_reporter/tests/test_contract_significance_policy.py
1a8920dff8f69129fc9f087e8f42ee5a3fac4d4dea586f01d14fc9b0b4c2054e  explora_web_reporter/tests/test_contract_universe_schema.py
9a7c036df7945c31df40d8c90056eb5cd27039278d4689fd5a249deafad6d7cd  explora_web_reporter/tests/test_contract_metric_schema.py
7f17e744fcf1aeaaf71ceef149016672e35c1457b58973a45208a2816ef35120  explora_web_reporter/tests/test_contract_canonical_result.py
984e65d435f3c39be4d06ead1ad97aae3690e1fb02a448d32af7651562e47d04  explora_web_reporter/tests/test_contract_renderer_neutrality.py
10206c67def366b8497c9778f55ef0512ea22ec317be8f56f14d8a88b51e217f  explora_web_reporter/tests/test_core_execution_mode.py
1d7bfb181e7949250a9a808c767cabf6a6e7b9f35d7967f72725eec37de8ef41  explora_web_reporter/tests/test_core_wrapper_parity.py
a4cadb852a4ea35185e1fe14ed2ab8bd751e52bf66cb47076a8938a311420fde  explora_web_reporter/tests/test_universe_evaluator.py
dc7998baa37ea2a6bcec91c97c4a9b6f685bf11e04dc6dde567c0d4f54938c76  explora_web_reporter/tests/test_universe_evaluator_response_states.py
54a5b5b8f0f8de8eccec95e7ad4b85132e194701ff93be63fba03fef9ba8e211  explora_web_reporter/tests/test_universe_evaluator_refs.py
ff4fec71e74ec961f2b8d067dbb2093f133f5b9a8f14adcf303c1b723f8b4b91  explora_web_reporter/tests/test_universe_evaluator_scopes.py
5fc109d3356d68963dc3a2d7919a4a7e919f5f3fec1ee6ab016a6f225329e9a1  docs/explora_target/EXPLORA_GATE1_CANONICAL.md
8181f65d8a3b4bf12bf6e19ff63015f07c34abe8b1e0c4fe1d61c5d78be73eed  docs/explora_target/WEIGHT_POLICY_CANONICAL.md
b9a70af23fa931ebbe9f3b7b4baacba549c69b2b1c2d6f03f033bb134bd883da  docs/explora_target/SIGNIFICANCE_POLICY_CANONICAL.md
e167b04a4ae564acc07c5e6e5784154bbbf502c9cc6d162b53d318b145a87e02  docs/explora_target/AI_RELEASE_POLICY_CANONICAL.md
22e54c79e4cbf4966e6e5c176b3215c82680c9bf749ee41e321d31688bc23fda  docs/explora_target/04_FINAL_CONTRACT_READINESS.md
67c200bfe1c2b3c4f7b62cbc4e9966cf44f9abf010efeb11eba88b8a844aaf6b  docs/explora_target/06_IMPLEMENTATION_MILESTONE_M0_M1_DRAFT.md
cc875da43127d95c25c73f738217d94b19c513d1a47badbb828f3cb5eb758a80  docs/explora_target/08_GATE1_FINAL_ASSESSMENT.md
7424cfd60449d01d0388e5f04dc3ae3a8f5c27eff175ee7e45b674711edafa6a  docs/explora_target/M1A_CONTRACT_FREEZE.md
c97a803bc3e50985471ad60f550395e333ea2902ac2f44a16cc7264c8cbc91f0  docs/explora_target/M1A_CONTRACT_FREEZE_MANIFEST.md
f1b3c754e5a95362d59801219b486f3728bbd6214a986792c647264ff0decf72  docs/explora_target/M2_UNIVERSE_EXECUTION.md
```
