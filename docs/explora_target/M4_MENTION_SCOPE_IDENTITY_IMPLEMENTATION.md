# M4 Mention Scope Identity V1 Implementation

Gate: 26 - M4 Mention Scope Identity Implementation Authorization

Base main SHA: `8d7781d3e46d4579a88d0cfdae48905774795874`

Feature branch: `feature/m4-mention-scope-identity`

## Scope

This implementation introduces typed M4 mention denominator scope identity.
It is an identity, representation, validation, and scope-resolution change only.

No intended numerical methodology change was made to:

- M2 Universe
- M3 Weight
- M4 respondent denominator mathematics
- M4 mention denominator mathematics
- duplicate policy
- exclusive policy
- zero-base behavior
- M5 formulas
- M6 Web behavior
- Legacy behavior
- SQLite behavior
- significance methodology
- Canonical Materialization

## Contract Additions

- `MentionScopeType`
  - `PARENT_RM`
  - `ROW`
  - `ENTITY`
  - `LOOP_INSTANCE`
  - `RELEASED_GROUP` remains reserved / unsupported V1.
- `MentionScopeIdentity`
  - `schema_version`
  - `scope_type`
  - `scope_ref`
- `StructureSpec.mention_denominator_scope` now resolves to typed identity for canonical execution.
- `DenominatorLedger` preserves `structure_id`, `requested_scope_identity`, and `resolved_scope_identity`.

## Compatibility Boundary

Historical string inputs are normalized before analytical execution:

- `structure`, `parent_structure`, `all_options` -> `PARENT_RM + current StructureSpec.structure_id`
- `row` -> `ROW + null`
- `row:<id>` -> `ROW + <row_id>`
- `entity`, `row/entity` -> `ENTITY + null`
- `entity:<id>` -> `ENTITY + <entity_id>`
- `loop_instance` -> `LOOP_INSTANCE + null`
- `loop_instance:<id>` -> `LOOP_INSTANCE + <loop_instance_id>`

Unknown or malformed tokens fail closed. `parent_rm:Q_DELIVERY_APPS` is not normalized.

## M5 Adapter

M5 mention ledger selection now uses exact typed identity:

- schema version
- scope type
- scope ref
- structure identity

`scope_id` remains compatibility/display metadata only. M5 provenance preserves requested and resolved typed scope identity when present.

## Test Results

- Focused MSCOPE: `29 PASS / 0 FAIL / 0 SKIP`
- M4 regression: `88 PASS / 0 FAIL / 0 SKIP`
- M5 adapter regression: `44 PASS / 0 FAIL / 0 SKIP`
- M5 regression: `116 PASS / 0 FAIL / 0 SKIP`
- M6 regression: `97 PASS / 0 FAIL / 0 SKIP`
- Legacy parity: `3 PASS / 0 FAIL / 0 SKIP`
- Full regression: `479 PASS / 0 FAIL / 0 SKIP`

## Known Warnings

- Git line-ending warnings report that LF may be replaced by CRLF on future Git touches in this Windows worktree.
- Benchmark A corrective package was not created.
- Canonical Materialization remains stopped.
- Gate 19 remains blocked.
