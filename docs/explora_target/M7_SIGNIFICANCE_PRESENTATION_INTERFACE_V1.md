# M7 Significance Presentation Interface V1

Contract ID: M7_SIGNIFICANCE_PRESENTATION_INTERFACE_V1. Status: FROZEN.
Core owns tests, families, multiplicity policy, eligibility and statistical status.
Excel/VBA do not compute tests, p-values, corrections or significance thresholds.

## Canonical transport

Transport supplied SignificanceRelation fields unchanged:
comparison_id, question_id, metric_id, analytical_scope, family_id,
left_slice_id/right_slice_id, left_member_id/right_member_id, test_id/test_version,
confidence, status, raw_p_value, adjusted_p_value, direction, qa_refs/provenance_refs.
Group identity is the supplied family/slice/member tuple, never cell adjacency.
SIGNIFICANT / NOT_SIGNIFICANT / INELIGIBLE / UNSUPPORTED / NOT_TESTED / FAIL
retain their exact canonical meanings; no new statistical enum.
Missing direction stays absent. Do not infer it from estimates or p-values.
Comparison references must resolve within the bound canonical run/family/scope.

## Supplied presentation tokens

Existing SignificanceRelation has no letter-token field. V1 defines a separate
presentation envelope, not a Core schema extension or an implemented producer:
schema_version, token_set_id, revision, authority_ref, result_run_id,
result_fingerprint, comparison_bindings and legend.
Each binding carries comparison_id, family_id, test_id/test_version, target
value_id/slice_id/member_id, supplied direction where present, token_id and literal
display_text. legend binds token IDs to supplied meanings and comparison refs.
The envelope is checksum-pinned as a Visual Spec reference and supplied by an
authorized upstream presentation producer/human-reviewed artifact.

Validate identity consistency against supplied comparisons, source status and
target records. Tokens attached to non-significant, unsupported or absent
comparisons cannot assert significance. Unresolved/contradictory refs fail closed.
Excel may place validated supplied tokens only; it cannot manufacture A/B letters,
assign comparison groups, infer direction or invent legend meanings.
Absent tokens: LETTER_DISPLAY_UNSUPPORTED renderer annotation, while preserving
available canonical relationship/status. This is not Core StatisticalState.
If a visual explicitly requires letters, missing envelope blocks that visual's
required render binding and official publication. No silent approximate letters.

## Not applicable and safety

NOT_APPLICABLE is a presentation annotation requiring explicit authority/reason,
not a replacement for a supplied UNSUPPORTED/NOT_TESTED status. No comparison
provided means no test evidence, not NOT_SIGNIFICANT. Display these distinctions
alongside canonical status/QA. Blocking QA remains visible and blocks release.
Tokens and legends obey literal safety; no formulas or macro statistical logic.
Future fixtures must cover available relationships with/without authorized tokens,
invalid family/target refs, missing direction, unsupported/ineligible/not-tested
states, non-significant relationships and malicious literal token text.

