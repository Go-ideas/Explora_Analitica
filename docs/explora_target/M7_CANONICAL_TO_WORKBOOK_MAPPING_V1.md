# M7 Canonical To Workbook Mapping V1

Contract ID: M7_CANONICAL_TO_WORKBOOK_MAPPING_V1. Status: FROZEN.
Inputs are validated CanonicalResult objects and existing serialization, not
Legacy ReportResult, CSV projections or respondent-level BD_Pivot.
Mapping is identity-preserving transport; no statistics or schema changes.

## Field/role mapping

| Canonical source | Workbook role / requirement |
| --- | --- |
| result_schema_version, result_run_id, result_fingerprint | provenance and every table run binding |
| project_id, dataset_fingerprint, project_spec_ref, core_version | provenance unchanged |
| manifest including ruleset/source_spec_refs and B1/B2/B3 refs | provenance and exact payload |
| request including request_id/fingerprint, metric_refs, question_ids | provenance/configuration snapshot |
| request.banner_config, filters, weight_override, execution_options | configuration audit; no execution in Excel |
| slices.slice_id/fingerprint, is_total | slices stable binding; totals copied, not summed |
| slices.banner_dimension_id/member_id/filter_refs/configuration/label | banner/filter identity and literal label |
| values.value_id/question_id/structure_id/slice_id | results identity |
| values.metric_id/formula_id/formula_version | metric identity, no executing formula |
| values.row_id/entity_id/column_id/option_id/category_id/loop_instance_id | explicit structural/category identities |
| values.base_id/value_status/unit/estimate/numerator/denominator | results exact source fields, never calculate estimate |
| values.semantic_order | source ordering; Visual Spec can explicitly rearrange presentation |
| values.significance_refs/qa_refs/provenance_refs | linked transport IDs |
| bases.base_id/question_id/structure_id/slice_id/universe_ref | bases identity |
| bases.denominator_unit/denominator_ref/denominator_scope_id | bases exact scope; never infer from label |
| bases.unweighted_n/weighted_n_raw/weighted_n/effective_n | separate columns; effective_n QA-only |
| bases.active_weight_ref/base_status and structural IDs | weighting/status identity, no recomputation |
| bases.qa_refs/provenance_refs | linked audit references |
| comparisons | significance transport under significance interface |
| qa / qa_events | qa table, exact states/blocking/scopes/messages/related IDs/details |
| release | provenance, official publication eligibility and reasons |
| supersedes_result_run_id | provenance lineage |
| complete existing serialized result | canonical_payload ordered chunks and checksum |

Missing optional fields remain null/absent as serialized; do not infer them.
Never select legacy compatibility base_records/value_records/significance_records
as a replacement for missing required official structured records.

## Labels, unsupported and adapters

Labels come from Visual Spec or explicitly supplied released Project Spec metadata
and are keyed by IDs. CanonicalValue has no universal question/response label field.
Absent label displays a technical ID with a diagnostic, not a fabricated label.
Weight indicator means active_weight_ref presence from source, not a guess from
fractional n. Banner/filter IDs are source refs, not new local analytical predicates.
RM mention/respondent denominator distinctions remain intact. Grid/Loop axes are
transported only where upstream records support them; alias names do not establish
execution support for means, scores or other metrics.
Unsupported/null/suppressed/not-computed follow numeric profile sidecars; no zeros.

## Workbook provenance

Required render manifest: project_id, project_spec_ref, dataset_fingerprint,
result_run_id/fingerprint/schema/core_version, request identity/fingerprint and
available manifest ruleset/source refs; Visual Spec ID/version/checksum; Master
ID/version/input SHA256/interface; renderer version/build identifier; numeric and
significance contract versions; canonical release/QA; render outcome/diagnostics.
Store exact config snapshot/checksum and all supplied input results. Missing
optional source versions are explicitly UNAVAILABLE, not guessed from filenames.
Required project/result/request/Master/spec/build identities must resolve or fail.
Render identity is separate from canonical result fingerprint.
Chunk payload below workbook string limits (maximum 32767 characters per cell),
with ordered chunk IDs, encoding, total length and exact reassembly checksum.
No truncation of payload, warnings or long text; capacity failure blocks release.

## Determinism oracle

Identical canonical payloads + Visual Spec bytes + controlled Master bytes +
renderer build/version must yield equivalent normalized workbook content.
Explicit significance token envelope and referenced label metadata are pinned
parts of Visual Spec inputs, never hidden mutable dependencies.
Normalize by role/slot and source ID: exact typed scalars/text/statuses, destinations,
row order, number formats/styles, tables/names/relationships, provenance and QA.
Compare canonical reassembly checksum and preserved VBA/package-part hashes.
ZIP ordering/compression and explicitly listed generation timestamp are excluded;
no analytical field, input checksum or formula may be excluded. Volatile metadata
is isolated from input/result identities. Duplicate render tests, label changes,
slice-order perturbations, capacity failures and stale-cell replacement tests are
required future M7D evidence. Byte-identical ZIP files are not the content oracle.

