# Gate 49 Loop Capability Contract

## Current State

M4 `StructureSpec`, validation, normalization, denominator ledgers and canonical identities already recognized `LOOP_RU`, `LOOP_RM` and `LOOP_NUMERICO`, requiring explicit loop-instance identity. The formula registry admitted `LOOP_RU` and `LOOP_NUMERICO`, and Canonical Results preserved `loop_instance_id`. However, Gate 47 authoring accepted only RU/RM, the materialization adapter discarded loop IDs, the execution adapter aggregated LOOP_RU across iterations and did not execute numeric formulas, and numeric materialization was checked as a categorical domain. Generic Productive Runtime consequently had no package-authored LOOP path. Existing tests covered isolated M4/M5 identities, not the complete authoring-to-runtime flow.

## Target State And Gap

`LOOP_RU` is one logical categorical question repeated over ordered iterations. `LOOP_NUMERICO` is one logical numeric measure repeated over ordered iterations. Iterations are neither RM options, unrelated questions nor banners. The parent `question_id` remains constant; every base/value carries `loop_instance_id`.

The Execution Release structure must provide `loop_iterations`, each with exactly:

- `iteration_id`: stable identity;
- `order`: unique contiguous one-based order;
- `label`: source label when available, otherwise an explicit reviewed label;
- `variable_ref`: one physical member variable;
- `response_domain`: the complete category domain for LOOP_RU and empty for LOOP_NUMERICO.

`variable_bindings` must bind each variable to the same `loop_instance_id`; membership must equal Project Spec `source_variables`. Duplicate identity/order/variable, missing source variables, incomplete membership, incompatible RU domains, categorical numeric domains and absent parent identity fail closed.

## Canonical Semantics

Each iteration inherits the question universe, request, weight choice and B3 envelope. LOOP_RU reuses Core proportion/count semantics per iteration and category. LOOP_NUMERICO reuses Core mean semantics per iteration. Missing values are excluded under the released missing policy. Weighted execution uses B1-resolved respondent weights and emits per-iteration `unweighted_n`, `weighted_n_raw`, `weighted_n` and `effective_n`; weighted mean calculation resides in the Core formula registry.

Canonical identity includes logical question, structure, request/slice/metric/formula and loop instance. Iteration order drives semantic order. Provenance includes package/runtime authorities plus `loop_instance:<id>`. Package and result fingerprints remain deterministic under existing canonical serialization.

## Decision

Gate 49 qualifies `LOOP_RU` and `LOOP_NUMERICO`. `LOOP_RM` remains fail-closed in generic authoring: existing Core primitives do not by themselves settle project-specific selected/not-selected, option-by-iteration, mention denominator and duplicate semantics. Loop significance also remains fail-closed pending a separately qualified per-iteration B2 family contract. No Core B1/B2/B3 authority or Web/Excel calculation boundary changes.
