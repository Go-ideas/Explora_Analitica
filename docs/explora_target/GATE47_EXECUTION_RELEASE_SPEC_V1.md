# Gate 47 Execution Release Spec V1

Schema ID: `EXPLORA_PROJECT_EXECUTION_RELEASE_V1`

## Contract

The root is an exact object containing `schema_version`, release identity and
version, project identity and exact Project Spec fingerprint, package settings,
source authority, policy identities, B3 release decision, and explicit arrays for
questions, structures, metrics, weights, banners, filters, significance and
one-question requests.

`package.internal_project_name` is mandatory ER authority. Project Spec
`display_name`, filenames and project IDs are not fallbacks.

Accepted policy identities are `B1_V1`, `B2_V1`, `B3_V1`, and
`M5_FORMULA_REGISTRY_V1`. The package execution compatibility declaration is
`LEGACY`; productive execution remains explicitly compiled as `CANONICAL_V1`.

## Explicit Authority

ER owns project-specific analytical roles, structure and formula selections,
physical-binding intent, response-state and denominator semantics, request
decomposition, release weight choices, configured banner/filter members,
significance families, and B3 provenance. Project Spec owns intake identities and
source mappings. B1, B2 and Core own methodology. B3 owns RELEASED status.

Logical variable references are joined exactly to Project Spec `source_name`
values. Labels and observed data are never binding authority. Each analytical
request carries `output_request_ref` and exactly one `question_ref`. All questions
in one Project Spec output request must be covered exactly once by explicit ER
requests. The backward-compatible 1:1 form may omit `output_request_ref` only
when `request_id == output_request_id`.

## Fail Closed

Validation rejects schema, project, fingerprint, source or policy mismatch;
unapproved B3 release; duplicate or dangling identities; unknown formulas;
unsupported or incomplete structures; implicit RM options; incomplete response
states or denominator behavior; silent unweighting; incomplete B2 families;
unsupported sample relationships; implicit request splitting; unresolved Project
Spec ambiguities or analytical AI decisions; and statistical-result fields.

## Serialization

JSON uses UTF-8, ASCII escaping, sorted keys and compact separators. Each record
hash excludes its own `spec_hash`. Package semantic identity hashes the exact
canonical bytes of files 01-09. `MANIFEST.json` inventories those non-self-
referential files and records Project Spec identity, source identities, B3
decision and runtime flags fixed false at authoring.

ZIP entries follow `PACKAGE_FILES` order, DEFLATE level 9, DOS timestamp
1980-01-01 00:00:00, Unix regular-file mode 0644, and no extra files. Publication
uses a sibling temporary file, current-loader round trip, and atomic replace.

## Prohibitions

Authoring does not parse source data, infer analytical configuration, calculate
statistics or eligibility, generate Canonical Results, silently select Legacy,
or contain Benchmark A, ATLAS, customer, question, metric, request or weight IDs.

## Qualified Execution Profile

| Capability | Gate 47 status |
| --- | --- |
| RU | SUPPORTED; package, materialization and runtime proven |
| RM | SUPPORTED; explicit option/state/denominator/scope package and materialization proven |
| PARENT_RM | FAIL-CLOSED / NOT YET QUALIFIED |
| MENTION | FAIL-CLOSED / NOT YET QUALIFIED |
| NUMERIC | FAIL-CLOSED / NOT YET IMPLEMENTED |
| SCALE | FAIL-CLOSED / NOT YET IMPLEMENTED |
| GRID_ESCALA | FAIL-CLOSED / NOT YET IMPLEMENTED |
| GRID_RM | FAIL-CLOSED / NOT YET IMPLEMENTED |
| LOOP_RU | FAIL-CLOSED / NOT YET IMPLEMENTED |
| LOOP_RM | FAIL-CLOSED / NOT YET IMPLEMENTED |
| LOOP_NUMERICO | FAIL-CLOSED / NOT YET IMPLEMENTED |
| Universe `in`, `not_in`, `eq`, `neq` | SUPPORTED |
| Universe `true`, `and`, `or`, `not`, comparisons and response-state operators | FAIL-CLOSED / NOT YET IMPLEMENTED by the builder serializer |

This is an authoring profile, not a claim that Core lacks other capabilities.
Unsupported intake configurations are rejected before package publication.

## B2 Serialization Authority

ER supplies significance identity, bindings, family members, sample relationship,
confidence, weight compatibility and supported test family. The builder creates
and validates the frozen `contracts.models.SignificanceSpec`; its machine-readable
B2 V1 defaults supply test identities/versions, alpha, sidedness, eligibility
rules, HOLM adjustment, family scope, total exclusion and unsupported behavior.
ER cannot override those methodology fields.

## RM explicit empty ordinary-missing shared contract corrective (2026-10-06)

Status: BOUNDED CONTRACT CORRECTIVE / CLARIFICATION, pending Human Review / Git
Adoption. Starting main: `2380cb79df36109ee4a3216834a96d27c6571be6`.
Branch: `fix/gate51-rm-empty-ordinary-missing`.

RM `selected_values` and `not_selected_values` are explicit required lists/tuples
and must be non-empty. `ordinary_missing_values` is also an explicit required
list/tuple but MAY be empty. Explicit `[]` means no additional ordinary-missing
physical response state exists; it is not absent, unknown, inferred or fallback
authority. Complete response-state authority means all three fields are explicitly
present and valid, rather than all three domains containing a value.

Canonical serializability, deterministic authoring order, duplicate-state
rejection in authoring, pairwise disjointness and fail-closed validation remain.
The shared package validator explicitly checks container types and retains
non-empty selected/not-selected domains. The Operator Console placeholder is
`[]`; its actual initial value stays blank, valid JSON must be entered, and
explicit human RM confirmation remains mandatory.

Builder, loader, materializer and formulas are unchanged. Synthetic coverage
checks empty and non-empty missing package paths, released-array preservation,
loader roundtrip, materialization and canonical RM results. An observed third
state not in selected/not-selected fails category-domain reconciliation when
missing is `[]`; explicitly declaring that state in missing permits it.

Package compatibility declaration remains `LEGACY`; productive execution remains
`CANONICAL_V1`. This corrective changes no execution-mode contract, rollback,
DUAL_RUN, option identity, denominator, PARENT_RM scope, completion policy,
storage encoding, missing calculation policy, B1/B2/B3 or analytical capability.
Only synthetic generic fixtures are used; no customer source data is committed.
