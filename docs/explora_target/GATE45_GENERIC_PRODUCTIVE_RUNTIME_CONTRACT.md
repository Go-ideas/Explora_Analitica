# Gate 45 Generic Productive Runtime Contract

## CURRENT STATE

Accepted analytical and presentation contracts remain authoritative. This contract adds orchestration and binding only.

## TARGET STATE

`run_generic_productive` consumes an accepted Project Spec, physical source, released execution package, output destination, and, for Excel, an accepted presentation configuration plus qualified Master.

## GAP

Visual Spec V1 requires concrete Canonical result-run identities, which exist only after execution. Project configuration starts with stable request identities.

## DECISION

`EXPLORA_PRODUCTIVE_PRESENTATION_V1` maps configured `request_id`, canonical record role/id/field and qualified `slot_id` into Visual Spec V1 after Core execution. Required fields are schema/configuration/project/visual identities, revision, slot IDs, sections and provenance references. Unknown fields, requests, slots or missing bindings fail closed.

## IMPLEMENTATION

- Input Project Spec must validate `READY_FOR_EXECUTION`; it is never reconstructed from the package.
- Current physical execution supports `SAV` only. Other accepted intake types fail closed until Core support is separately qualified.
- Output intent is the union of per-request `web_included` and `excel_included`; an empty intent fails closed.
- Core executes through CANONICAL_V1 with exact source/package fingerprints and no Legacy fallback.
- Web uses `project_canonical_result` with project identity and performs no calculations.
- Excel uses existing `RenderRequest`, Visual Spec V1, qualified slots, `plan_render` and `render`; physical numeric read-back must equal Canonical Results.
- Weights, universes, banners, filters and B1/B2/B3 identities remain in the compiled execution binding. No reference is silently dropped or repaired.
- Release names normalize configured identity only: `<project_id>[__<configuration_id>]`; Excel appends `.xlsm`.
- Publication is atomic: build in sibling staging and rename only after all QA passes.
- Provenance records Project Spec version/fingerprint, source/package hashes, binding/Core/result identities, presentation identity, Web/Excel identities, Master/VBA identities, QA and release fingerprint.

## VALIDATION

WEB-only, EXCEL-only and WEB+EXCEL are covered. The non-Benchmark synthetic fixture exercises fixed-slot Excel and exact VBA preservation. Significance and Dynamic Region are `NOT EXERCISED`; their accepted contracts are unchanged.
