# Gate 46 Project Spec to Package Crosswalk

## Classification and decision vocabulary

Source classifications are exhaustive: `A` exactly in Project Spec; `B`
deterministically derivable from it; `C` supplied by an accepted policy/Core
contract; `D` explicit new `EXPLORA_PROJECT_EXECUTION_RELEASE_V1` configuration;
`E` human/B3 release decision; `F` unsupported or contract gap. Decision classes
are `DETERMINISTIC`, `AI-PROPOSED`, `HUMAN-APPROVED`, `POLICY-DERIVED`,
`STATISTICAL-RESULT`, and `PRESENTATION-ONLY`.

The target authority abbreviation `ER` means the new Execution Release Spec.
`B3` means its human/release envelope. A slash in Source means all named inputs
are required. Every observed field path in the ten loader-required package files
is included below; dynamic object keys are represented by `<id>`.

## 01_PROJECT_SPEC_RELEASED.json

| Field(s) | Meaning/current authority | Source and transform | Missing/approval/B1-B3 | Fail closed | Target authority |
|---|---|---|---|---|---|
| `project_id`, `spec_version` | Project identity/version; released file | A; `project.project_id`, `project.spec_version` | B3 release required | Missing/mismatch | Project Spec + B3 |
| `internal_project_name` | Internal release name | A/D; display name may not be assumed internal | Explicit ER value; human if sensitive | Absent/ambiguous | ER |
| `spec_type`, `canonical_structure_authority` | Contract identities | C; fixed accepted constants | Policy-derived | Unknown value | Core contract |
| `release_state`, `productive_project` | Executable lifecycle/scope | E | Human/B3 decision | Anything but authorized RELEASED | B3 |
| `default_execution_mode` | Legacy/canonical mode declaration | D/C | Explicit ER under compatibility policy | Absent/unsupported mode | ER + runtime policy |
| `default_weight_ref` | Project default weight | A/D | Project Spec ref plus released B1 scope | Unknown/ambiguous | Project Spec + ER/B1 |
| `dataset.dataset_fingerprint_sha256` | Physical source identity | A/B; normalize `dataset.fingerprint` | None if valid SHA-256 | Invalid/mismatch | Project Spec |
| `dataset.dataset_version` | Frozen dataset release version | D | New explicit version | Missing | ER |
| `dataset.source_filename` | Audit display name | D | Source artifact metadata; never path authority | Missing when required | ER provenance |
| `dataset.row_count`, `dataset.fieldwork_target_from_questionnaire`, `dataset.snapshot_approved_for_benchmark` | Historical source observations/benchmark flags | F / STATISTICAL-RESULT or benchmark-only | Not authored; optional external QA evidence only | Required by a profile => unsupported | QA service, not package author |
| `dataset.derived_execution_artifact.type`, `.status` | Historical artifact annotation | D/E | Explicit extension only | Unknown extension | ER extension |
| `respondent_key.candidate_physical_variable` | Respondent binding | A/B; dataset respondent id -> source name | Human approval if fallback/absence | Unknown/duplicate binding | Project Spec + ER |
| `respondent_key.status` | Binding release status | E | B3 decision | Not approved | B3 |
| `question_spec_refs[*]`, `structure_spec_refs[*]`, `universe_spec_refs[*]`, `metric_spec_refs[*]`, `significance_spec_refs[*]`, `banner_spec_refs[*]`, `filter_spec_refs[*]`, `request_refs[*]` | Package reference inventory | B; sorted IDs from released artifacts | Depends on B1/B2/B3 artifacts | Missing, duplicate, dangling | Builder-derived |
| `grid_loop_scope.<id>` | Historical per-project scope note | F | No generic schema; omit until separately contracted | Required value => unsupported | Future contract |
| `provenance.*` | Shared source/release evidence; paths listed in Shared Envelope below | A/D/E | Merge Project Spec provenance, ER source fingerprints, B3 decision | Incomplete/conflicting | Project Spec + ER + B3 |
| `spec_hash` | Canonical file/spec fingerprint | B | Hash canonical content excluding self-hash | Mismatch | Builder |

## Shared provenance and release envelope

This row set applies wherever the same paths occur in files 01-09.

| Field(s) | Meaning/current authority | Source and transform | Missing/approval/B1-B3 | Fail closed | Target authority |
|---|---|---|---|---|---|
| `spec_type`, `spec_version` | Artifact contract/version | C/D; accepted type and ER version | Policy-derived; version explicit | Unknown version | Core contract + ER |
| `release_state` | Artifact lifecycle | E / HUMAN-APPROVED | B3 release decision | Not RELEASED | B3 |
| `provenance.human_decision_id`, `.human_decision_basis`, `.release_mode`, `.released_at` | Release decision trail | E | Required B3 decision, reason, mode, timestamp | Missing/unreleased | B3 |
| `provenance.mapping_authority`, `.methodology_authorities[*]` | Mapping/policy identities | C/D | Accepted contracts plus explicit mapper version | Unknown policy/version | ER + B1/B2/B3 |
| `provenance.authoritative_datamap` | Datamap authority | D/E | Artifact fingerprint/ref; human confirms revision | Missing where mapping is used | ER + B3 |
| `provenance.source_dataset.filename`, `.sha256`, `.rows`, `.spss_creation`, `.active_spss_weight` | Source evidence | A/D/F | Filename/hash from ER; rows/creation/active weight are external metadata, not calculated | Hash absent/mismatch; required observations unavailable | Project Spec + ER/QA |
| `provenance.source_questionnaire.filename`, `.sha256`, `.declared_revision`, `.authority_for_benchmark` | Questionnaire evidence | A/D/E | Project provenance + ER artifact record; authority flag human-approved | Missing/conflicting revision | ER + B3 |
| `spec_hash` | Artifact integrity | B / DETERMINISTIC | Canonical hash | Mismatch | Builder |

## 02_QUESTION_SPECS_RELEASED.json

| Field(s) | Meaning/current authority | Source and transform | Missing/approval/B1-B3 | Fail closed | Target authority |
|---|---|---|---|---|---|
| `[*].question_id` | Stable analytical question | A | `questions[].question_id` | None | Missing/duplicate | Project Spec |
| `[*].question_spec_id` | Released spec identity | B/D | Deterministic namespace rule frozen in ER contract | Collision | Builder + ER version |
| `[*].analytical_role` | Executable role | D/E | Explicit role; never inferred from label | Human approval for analytical role | Missing/unsupported | ER + B3 |
| `[*].physical_variable_bindings[*].variable_ref`, `.spss_short_name` | Logical/physical bindings | A/B | Join source variables to dataset variable/source name | Ambiguous mapping requires human decision | Unknown/duplicate | Project Spec |
| `[*].category_refs[*]` | Category identities | A/B | Question categories, normalized IDs/order | None unless recoded | Dangling/duplicate | Project Spec + ER if recoded |
| `[*].universe_ref` | Question universe | A | `questions[].universe_ref` | Human only for unresolved ambiguity | Dangling | Project Spec |
| `[*].structure_ref`, `[*].metric_refs[*]` | Executable structure/metrics | D | Explicit ER references | B1/B2 constraints apply downstream | Missing/dangling | ER |
| `[*].weight_behavior` | Metric/question weighting intent | D/C | Explicit behavior constrained by B1 | Human approves project choice | Missing/unsupported | ER + B1/B3 |
| `[*].label_metadata_only` | Label non-authority marker | B/C / PRESENTATION-ONLY | True unless an accepted contract says otherwise | None | False without authority | Builder policy |
| Shared envelope fields | Release and provenance | A/B/C/D/E | Shared Envelope | B3 | Incomplete | ER + B3 |

## 03_STRUCTURE_SPECS_RELEASED.json

| Field(s) | Meaning/current authority | Source and transform | Missing/approval/B1-B3 | Fail closed | Target authority |
|---|---|---|---|---|---|
| `[*].structure_id` | Executable structure identity | D/B | ER identity, deterministic namespace | Human approves semantic assignment | Missing/collision | ER |
| `[*].question_id`, `[*].structure_type` | Parent and structure family | A/D | Question ID; type mapping must be explicitly released | Type cannot be guessed from labels | Missing/unsupported | Project Spec + ER |
| `[*].variable_bindings[*].variable_ref`, `.spss_short_name` | Non-RM physical binding | A/B/D | Explicit ER roles joined to source names | Complex axes require ER | Unknown/ambiguous | ER + Project Spec |
| `[*].option_bindings[*].option_id`, `.variable_ref`, `.spss_short_name`, `.label` | RM option binding | D/A/PRESENTATION-ONLY | Explicit option identity/binding; label from intake only | Human approves option semantics | Any inferred option | ER + Project Spec |
| `[*].category_bindings[*].category_id`, `.raw_value`, `.label` | Raw-to-category binding | A/D | Exact intake category when one-to-one; recodes require ER | Human approval for recodes/exclusions | Contradiction/implicit recode | Project Spec + ER/B3 |
| `[*].applicability_refs.<role>` | Applicability universe by role | D/A | Explicit role-to-universe map | Human if not exact intake rule | Missing/dangling | ER |
| `[*].selected_values[*]`, `.not_selected_values[*]`, `.ordinary_missing_values[*]` | RM/response-state semantics | D/E | Explicit values; no inference from observed data | Human approves analytical semantics | Missing/overlap | ER + B3 |
| `[*].completion_policy`, `.storage_encoding`, `.duplicate_policy`, `.response_state_version` | Structure execution policies | D/C | Explicit ER values constrained by M4 contract | Human if project-specific | Missing/unsupported | ER + M4 |
| `[*].exclusive_option_ids[*]`, `.exclusive_scope` | Exclusive behavior | D/E | Explicit option IDs/scope | Human approval | Implicit exclusivity | ER + B3 |
| `[*].respondent_denominator_behavior`, `.mention_denominator_behavior` | Denominator semantics | D/C/E | Explicit Metric/Structure release, constrained by M4 | Analytical human approval | Missing/contradictory | ER + M4/B3 |
| `[*].mention_denominator_scope.{schema_version,scope_type,scope_ref}`, `[*].m4_mention_scope_identity.{schema_version,scope_type,scope_ref}` | Typed mention scope identity | D/C | One canonical ER value serialized to compatibility aliases | M4 authority | Untyped/unsupported | ER + M4 |
| `[*].structural_zero_provenance`, `.structural_missing_semantics` | Structural response provenance | D/E | Explicit semantic evidence | Human approval | Missing where required | ER + B3 |
| `[*].observed_source_qa.row_count`, `.exclusive_violations_observed`, `.missing_by_option.<option_id>` | Historical observed source QA | F / STATISTICAL-RESULT | Not produced by authoring; optional external QA attachment | No analytical release authority | Required => unsupported | Runtime/source QA |
| `[*].corrective_release.{blocker_id,reason,released_at,previous_untyped_scope,canonical_scope_identity.schema_version,canonical_scope_identity.scope_type,canonical_scope_identity.scope_ref}` | Historical corrective lineage | D/E | Optional B3 lineage extension | Human-approved if present | Partial lineage | B3 history |
| Shared envelope fields | Release/provenance/integrity | A/B/C/D/E | Shared Envelope | B3 | Incomplete | ER + B3 |

## 04_UNIVERSE_SPECS_RELEASED.json

| Field(s) | Meaning/current authority | Source and transform | Missing/approval/B1-B3 | Fail closed | Target authority |
|---|---|---|---|---|---|
| `[*].universe_id` | Stable universe identity | A | `universes[].universe_id` | None | Missing/duplicate | Project Spec |
| `[*].expression.op`, `.variable_ref`, `.values[*]` | Current limited serialized expression | A/B | Convert structured operator/args only through lossless operator mapping | Human if ambiguity | Unsupported operator/lossy mapping | Project Spec + Core grammar |
| `[*].level` | Project/question/slice level | A/D | `execution_scope` mapping frozen by ER | Human if semantic scope changes | Missing/unknown | Project Spec + ER |
| `[*].missing_policy`, `.on_unresolved` | Universe execution failure policy | C/D | Explicit ER constrained to fail-closed policy | None for accepted default | Permissive/unknown | ER + M2 |
| `[*].source_text` | Audit-only source wording | D/PRESENTATION-ONLY | Optional metadata reference, not parser authority | None | Used as executable rule | ER provenance |
| `[*].interpretation.confidence`, `.human_approved`, `.requires_review` | Interpretation decision | A/E | AI interpretation plus B3 decision | Human approval when required | Unresolved critical review | Project Spec + B3 |
| Shared envelope fields | Release/provenance/integrity | A/B/C/D/E | Shared Envelope | B3 | Incomplete | ER + B3 |

## 05_WEIGHT_REGISTRY_RELEASED.json

| Field(s) | Meaning/current authority | Source and transform | Missing/approval/B1-B3 | Fail closed | Target authority |
|---|---|---|---|---|---|
| `registered_weights[*]` | Released WeightSpec records, empty in benchmark | A/C/D/E | Project candidates plus complete B1 fields and B3 release envelope | B1 sole methodology; human selects scope | Missing config never becomes unweighted | ER + B1/B3 |
| `project_default_weight_ref` | Project default | A/D | `default_weight_ref` plus released registry check | Human approves project default | Unknown/ambiguous | Project Spec + ER |
| `analysis_specific_overrides[*]` | Allowed request overrides | D/E | Explicit request-to-weight rules | B1 validation + human approval | Implicit override | ER + B1/B3 |
| `explicitly_unweighted_requests[*]` | Deliberate unweighted execution | D/E | Explicit request IDs | Human approval required when weights exist | Omission/unknown request | ER + B3 |
| `resolution` | Weight resolution statement | B/C | Deterministic summary of explicit registry/default/overrides | B1 | Contradiction | Builder + B1 |
| `source_qa.active_spss_weight`, `.weight_candidate_columns_authorized[*]` | Source metadata/authorization | D/E/F | External metadata and explicit authorization; no data inference | Human approves candidate list | Used as silent default | ER + B3/source QA |
| Shared envelope fields | Release/provenance/integrity | A/B/C/D/E | Shared Envelope | B1/B3 | Incomplete | ER + B1/B3 |

## 06_METRIC_SPECS_RELEASED.json

| Field(s) | Meaning/current authority | Source and transform | Missing/approval/B1-B3 | Fail closed | Target authority |
|---|---|---|---|---|---|
| `[*].metric_id`, `.metric_type` | Metric identity/family | D/E | Explicit ER selection from accepted registry | Human approves project metric | Missing/unknown | ER + Core registry/B3 |
| `[*].formula_id` | Core formula authority | C/D | Explicit accepted formula reference; never generated from label/type alone | Core sole calculation authority | Unknown formula | ER + Core registry |
| `[*].question_ref`, `.universe_ref` | Metric analytical scope | A/D | Explicit ER references | Human if differs from question default | Missing/dangling | ER |
| `[*].denominator_policy`, `.missing_behavior`, `.weight_behavior` | Analytical semantics | C/D/E | Explicit released values constrained by Core/B1/M4 | Human approval for project choice | Absent/unsupported/conflicting | ER + Core/B1/B3 |
| `[*].parameters.category_id`, `.raw_value`, `.category_scope`, `.respondent_option_deduplication` | Metric-specific configuration | A/D/E | Exact category data plus explicit scope/dedup semantics | Human approval where analytical | Missing for formula | ER + B3 |
| `[*].parameters.mention_denominator_scope.{schema_version,scope_type,scope_ref}`, `[*].m4_mention_scope_identity.{schema_version,scope_type,scope_ref}` | Typed RM mention scope | D/C | Explicit canonical ER scope serialized compatibly | M4 authority | Untyped/missing | ER + M4 |
| `[*].significance.status`, `.supported`, `.test_family`, `.enabled_for_benchmark`, `.reason` | Metric inference eligibility/annotation | C/D/E/F | B2 policy + explicit request; benchmark flag is historical and omitted generically | B2 and human release | Guessed eligibility | ER + B2/B3 |
| `[*].corrective_release.{blocker_id,reason,released_at,previous_untyped_scope,canonical_scope_identity.schema_version,canonical_scope_identity.scope_type,canonical_scope_identity.scope_ref}` | Corrective lineage | D/E | Optional B3 history | Human if present | Partial lineage | B3 history |
| Shared envelope fields | Release/provenance/integrity | A/B/C/D/E | Shared Envelope | B1/B2/B3 | Incomplete | ER + B3 |

## 07_SIGNIFICANCE_SPECS_RELEASED.json

| Field(s) | Meaning/current authority | Source and transform | Missing/approval/B1-B3 | Fail closed | Target authority |
|---|---|---|---|---|---|
| `[*].significance_id`, `.request_ref`, `.question_ref`, `.metric_ref`, `.banner_ref` | Project inference identity/scope | A/D/E | Intent plus explicit one-request family configuration | Human approves family scope | Missing/dangling | ER + B3 |
| `[*].confidence` | Requested confidence | A | Significance request | B2 validates | Unsupported value | Project Spec + B2 |
| `[*].alpha` | Complement of confidence | B/C | Deterministic B2 transform | B2 | Mismatch | Builder + B2 |
| `[*].test_identity`, `.test_version`, `.sidedness`, `.multiple_comparison_adjustment` | Frozen inferential method | C | Exact B2 policy constants/registry | B2 sole authority | Unknown/mismatch | B2 |
| `[*].sample_relationship` | Independence/paired identity | D/E/C | Explicit ER value allowed by B2 | Human approval; never inferred | Missing/unsupported | ER + B2/B3 |
| `[*].comparison_family_id`, `.family_members[*]`, `.total_in_family` | Multiplicity family | D/E/C | Explicit family membership under B2 rules | Human approves requested analytical scope | Implicit family/singletons | ER + B2/B3 |
| `[*].eligibility_rules.minimum_unweighted_n_per_group`, `.minimum_expected_successes`, `.minimum_expected_failures`, `.evaluated_again_at_runtime` | Eligibility policy | C | Serialize B2 V1 constants | B2 | Divergence | B2 |
| `[*].weight_ref` | Inference weight | D/C | Explicit null in B2 V1; no weighted inference | B1/B2 | Non-null unsupported | ER + B2 |
| `[*].unsupported_cases_preserved[*]` | Explicit unsupported inventory | C/B | B2 policy set | B2 | Silent fallback | B2 |
| `[*].source_snapshot_precheck.precheck_status`, `.[<member>].n`, `.successes_raw_code_5`, `.failures` | Historical precomputed observations | F / STATISTICAL-RESULT | Never authored; runtime B2 computes eligibility | None for package authority | Required => unsupported | Runtime B2 evidence |
| Shared envelope fields | Release/provenance/integrity | A/B/C/D/E | Shared Envelope | B2/B3 | Incomplete | ER + B2/B3 |

## 08_BANNER_FILTER_SPECS_RELEASED.json

| Field(s) | Meaning/current authority | Source and transform | Missing/approval/B1-B3 | Fail closed | Target authority |
|---|---|---|---|---|---|
| `banners[*].banner_id`, `filters[*].filter_id` | Stable rule identity | A | Project Spec IDs | B3 availability approval | Missing/duplicate | Project Spec + B3 |
| `banners[*].physical_variable_ref`, `filters[*].physical_variable_ref` | Physical binding | A/B | Variable ref -> source name binding | None if exact | Unknown/ambiguous | Project Spec |
| `banners[*].dimension_id`, `filters[*].dimension_id` | Canonical slice dimension | D/B | Explicit ER or frozen namespace rule | Human if semantic grouping | Collision/missing | ER |
| `banners[*].members[*].member_id`, `.raw_value`, `.label`; `filters[*].members[*].member_id`, `.raw_value`, `.label` | Released member domain | A/D/E | Rule/category data plus explicit IDs/order; labels metadata only | Human approves grouping/recode | Implicit grouping/unknown value | Project Spec + ER/B3 |
| `banners[*].mode`, `.default_selected` | Banner execution/default behavior | D/E | Explicit ER; B3 says default comparison is manual | Human approval | Implicit default | ER + B3 |
| `filters[*].default_application` | Default filter activation | D/E | Explicit null unless manually approved | B3 manual | Silent default | ER + B3 |
| `multi_filter_used_productively` | Historical execution claim | F | Runtime evidence, not authoring config | None | Used as authority | Runtime QA |
| Shared envelope fields | Release/provenance/integrity | A/B/C/D/E | Shared Envelope | B3 | Incomplete | ER + B3 |

## 09_REQUEST_MATRIX_RELEASED.json

| Field(s) | Meaning/current authority | Source and transform | Missing/approval/B1-B3 | Fail closed | Target authority |
|---|---|---|---|---|---|
| `matrix_id` | Released matrix identity | D/B | ER identity/versioned namespace | B3 release | Missing/collision | ER |
| `requests[*].request_id` | One-question analytical request | D | Explicit ER records; no implicit splitting | Human approves matrix | Missing/duplicate | ER + B3 |
| `requests[*].question_ref` | Single question | A/D | Explicit selection from output request questions | Splitting/order human-approved | Multiple/unknown | ER |
| `requests[*].metric_refs[*]` | Requested executable metrics | D | Explicit ER references | Core/B1/B2 constraints | Empty/dangling | ER |
| `requests[*].universe_ref` | Request universe | A/D | Explicit ER, may equal question universe only when stated | Human for override | Missing/dangling | ER |
| `requests[*].weight_ref` | Request weight | D/E/C | Explicit weight or explicit null | B1 + human decision | Silent unweighted fallback | ER + B1/B3 |
| `requests[*].filters[*].filter_ref`, `.member_ids[*]` | Applied filters/members | A/D/E | Output intent plus explicit members; refs alone are insufficient | Human approves application | Implicit members/default | ER + B3 |
| `requests[*].banner.banner_ref`, `.member_ids[*]` | Applied banner/members | A/D/E | Output intent plus explicit comparison members | B2/B3 if significance | Implicit members | ER + B2/B3 |
| `requests[*].significance_ref`, `.significance_status` | Inference configuration/status | A/D/C/E | Explicit released SignificanceSpec or null + reason | B2/B3 | Missing when requested/silent fallback | ER + B2/B3 |
| `requests[*].purpose` | Audit description | D/PRESENTATION-ONLY | Explicit metadata, never semantic authority | None | Used to infer config | ER metadata |
| `multi_filter_request` | Historical special request pointer | D/F | Optional explicit extension; not inferred | Human if enabled | Unsupported shape | ER extension |
| Shared envelope fields | Release/provenance/integrity | A/B/C/D/E | Shared Envelope | B1/B2/B3 | Incomplete | ER + B3 |

## MANIFEST.json

| Field(s) | Meaning/current authority | Source and transform | Missing/approval/B1-B3 | Fail closed | Target authority |
|---|---|---|---|---|---|
| `package_id`, `package_version` | Released package identity | D/E | ER identity/version approved for release | B3 | Missing/collision | ER + B3 |
| `project_id` | Project binding | A | Exact Project Spec ID | None | Mismatch | Project Spec |
| `dataset_fingerprint_sha256`, `questionnaire_sha256` | Source identities | A/D | Normalize Project Spec/ER artifact fingerprints | Human confirms authoritative revision | Missing/mismatch | Project Spec + ER |
| `status` | Package lifecycle | E | B3 sets `RELEASED` only after all validation | B3 | Not RELEASED | B3 |
| `released_at`, `human_decision_id` | Release audit | E | B3 decision | B3 | Missing | B3 |
| `default_execution_mode` | Execution compatibility | D/C | Explicit ER allowed mode | Runtime policy | Unsupported | ER |
| `dual_run_executed`, `canonical_result_generated`, `m7_started` | Historical execution claims | F / STATISTICAL-RESULT | False at authoring or omitted by target profile; never inferred from files | None | Claimed true without evidence | Runtime evidence, not authoring |
| `files[*].filename`, `.sha256`, `.size_bytes` | ZIP inventory/integrity | B | Deterministic post-serialization values for exactly ten required files | None | Missing/extra/hash mismatch | Builder |
| `spec_hash` | Package semantic fingerprint | B | Canonical hash over released semantic artifacts | None | Mismatch | Builder |
| `corrective_release.{blocker_id,reason,released_at,previous_untyped_scope,canonical_scope_identity.schema_version,canonical_scope_identity.scope_type,canonical_scope_identity.scope_ref}` | Optional corrective lineage | D/E | B3 history extension | Human if present | Partial lineage | B3 history |

## Coverage result

All ten `PACKAGE_FILES` and every observed required-package field path are
classified. There are no unclassified fields. Fields classified `F` are not
silently dropped: a target profile must either omit them as non-authoritative
historical evidence or fail closed if compatibility requires them.
