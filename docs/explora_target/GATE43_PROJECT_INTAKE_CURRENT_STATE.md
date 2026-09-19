# Gate 43 Project Intake Current State

## Audit Scope

The audit covered `src/contracts`, `src/analytics_core`,
`src/canonical_materialization`, `src/web_canonical`, `src/excel_renderer`, the
legacy database/reporter paths, released package manifests, tests, and the B1,
B2, and B3 canonical policies. The existing `contracts.models.ProjectSpec` is a
released Core execution binding. It is not a complete intake manifest and is
kept unchanged.

## Inventory

| Existing element | Owner / consumer | Classification | Gate 43 decision |
|---|---|---|---|
| `contracts.models.ProjectSpec` and `validate_project_spec` | Core contract validation | KEEP | Remains the narrow released execution binding downstream of intake. |
| `QuestionSpec`, `StructureSpec`, M4 validators | Core question/structure authority | KEEP | Project Spec V1 references only currently supported identities/types. |
| `UniverseSpec` and `analytics_core.universe` | M2 | KEEP | Structured universe expressions remain execution authority. Intake rejects natural-language-only rules. |
| `WeightSpec` and `analytics_core.weights` | M3 / B1 | KEEP | Intake validates references and B1 boundaries; it does not calculate or repair weights. |
| `SignificanceSpec` and `analytics_core.significance` | B2 / Core | KEEP | Intake carries requests and `B2_V1`; no test mathematics is duplicated. |
| `canonical_materialization` released package files | Materialization | ADAPT | Future adapter may compile an accepted Project Spec into these existing packages. Gate 43 does not execute that adapter. |
| `RequestSnapshot` banner/filter dictionaries | M5/M6/Web | ADAPT | Project Spec gives stable banner/filter identities before request binding. |
| Visual Spec, fixed slots, Dynamic Regions | M7 | KEEP | Output intent selects Web/Excel only; it cannot change analytical values. |
| SQLite `configuracion`, UI-selected filters and legacy reporter options | Legacy Web/reporter | DEPRECATE LATER | Still supported; not promoted to Project Spec authority automatically. |
| Builder factor-derived variables | Legacy builder | DEPRECATE LATER | Existing behavior remains. No unrestricted transform engine is introduced. |
| Benchmark A released manifests | Benchmark evidence | OUT OF SCOPE | Useful reference, never a universal project template. |
| Questionnaire/PDF/Word parsing, OCR and AI agent orchestration | Future intake | OUT OF SCOPE | Physical parsing is separate from semantic Project Spec V1. |

## Current Gaps

- No single pre-execution package binds source fingerprints, stable project and
  question identities, ambiguity decisions, outputs, and policy references.
- Existing execution contracts assume upstream release and do not represent
  `NEEDS_HUMAN_DECISION`.
- Legacy configuration is distributed across database tables, settings and
  materialization manifests.
- Derived-variable support is legacy/bounded and is not a general expression
  contract.

Gate 43 fills only this intake boundary. It does not replace existing execution
contracts or migrate legacy projects.
