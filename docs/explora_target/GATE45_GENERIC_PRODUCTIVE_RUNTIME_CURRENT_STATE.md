# Gate 45 Generic Productive Runtime Current State

## CURRENT STATE

Gate 44 proved the productive architecture on Benchmark A, but `project_intake/productive.py` combines a Benchmark package bootstrap, generic Core execution and a fixed Benchmark presentation. The accepted `ProjectExecutionBinding`, Canonical Materialization, Canonical Web adapter, `RenderRequest`, Visual Spec V1, qualified Master and Dynamic Region contracts already provide the reusable boundaries.

Gate 44 is CLOSED / ACCEPTED / MERGED through PR #17. Its official main is `c62145d546659a25e9d775cc634c813722cd8154`.

Assumption classification:

| Assumption | Classification | Gate 45 treatment |
|---|---|---|
| CANONICAL_V1, one Core result release, shared Web/Excel source | KEEP AS GENERIC | Preserved |
| Project Spec validation, package/source hashes, B1/B2/B3 refs | KEEP AS GENERIC | Preserved fail-closed |
| `build_project_spec(source, package)` | MOVE TO BENCHMARK FIXTURE | Gate 44 bootstrap only |
| `benchmark_a_request`, BA request selection, fixed FUNSMX filename | MOVE TO BENCHMARK FIXTURE | Not imported by generic runtime |
| Gate-specific Web presentation identity/runtime version | MOVE TO CONFIGURATION | Project/config identities used |
| forced WEB+EXCEL, decimals=6, weights=[], respondent `key` | MOVE TO CONFIGURATION | Project Spec/config authority |
| `universes[0]` presentation context | MOVE TO CONFIGURATION | No implicit universe selection |
| SAV physical execution | DEPRECATE LATER | Current Core constraint; unsupported types fail closed |
| Dynamic Region proportions beyond safe precision | BLOCKING GENERALIZATION GAP | No rounding; capability not exercised |
| Production Master slot coverage | BLOCKING GENERALIZATION GAP | Only declared qualified slots accepted |

## TARGET STATE

An already accepted `EXPLORA_PROJECT_SPEC_V1`, source, released package, optional accepted presentation configuration and qualified Master enter one project-neutral runtime. It emits Canonical Results and only the requested Web/Excel outputs, plus QA, provenance and a release manifest.

## GAP

There was no generic presentation binding from request identities to Visual Spec result runs and qualified slots. Gate 44 also reconstructed Project Spec from its release package and forced both surfaces.

## DECISION

Add `generic_productive.py` and a CLI. Keep Gate 44 unchanged as historical compatibility. Introduce only a narrow `EXPLORA_PRODUCTIVE_PRESENTATION_V1` binding envelope; it compiles into existing Visual Spec V1 and `RenderRequest`, not a competing renderer schema.

## IMPLEMENTATION

The runtime derives targets from Project Spec, executes CANONICAL_V1 twice, validates deterministic identities, publishes through staging, and derives names as `<project_id>[__<configuration_id>]`. WEB-only, EXCEL-only and combined output are supported. Excel requires explicit presentation configuration, qualified Master and Master artifact.

## VALIDATION

The synthetic `project_m6/request_m6` fixture is not a customer project. It proves neutral names and request identities, physical Excel read-back, Web parity, VBA preservation and atomic publication. Benchmark A remains regression evidence. Final test counts are recorded in the Gate 45 checkpoint and implementation review.
