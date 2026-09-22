# Gate 47 Execution Release Spec V1

Schema ID: `EXPLORA_PROJECT_EXECUTION_RELEASE_V1`

## Contract

The root is an exact object containing `schema_version`, release identity and
version, project identity and exact Project Spec fingerprint, package settings,
source authority, policy identities, B3 release decision, and explicit arrays for
questions, structures, metrics, weights, banners, filters, significance and
one-question requests.

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
values. Labels and observed data are never binding authority. A Project Spec
output request must correspond to one explicit ER request and one question;
multi-question splitting is never inferred.

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
