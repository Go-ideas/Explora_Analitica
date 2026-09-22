# Gate 46 Package Authoring Decision Register

## ADR-G46-01 - Authoring boundary

**Decision:** adopt Option B, additive
`EXPLORA_PROJECT_EXECUTION_RELEASE_V1`.

| Criterion | A: extend Project Spec | B: additive ER spec | C: existing contracts only | D: other |
|---|---|---|---|---|
| Single source of truth | Mixes intake and release concerns | Project Spec owns intake; ER owns executable release choices | Missing project-specific authority | No evidenced alternative |
| Duplication | High: repeats Core/B1/B2/B3 fields | References accepted registries/policies; stores only project choices | Low, but cannot represent choices | Undefined |
| Deterministic generation | Possible after broad schema expansion | Yes, from two fingerprinted inputs plus policy versions | No | Not demonstrated |
| Human approval | Blurs READY intake with RELEASED execution | Explicit B3 release envelope | No place for project release decisions | Undefined |
| B1/B2/B3 authority | Risk of copied methodology | Preserved by references and validators | Preserved but incomplete | Unproven |
| Backward compatibility | Requires Project Spec V2/migration | Additive; V1 and loader remain unchanged | Loader unchanged but builder blocked | Unproven |
| Traceability | One oversized artifact | Clear Project Spec + ER + package lineage | Missing release lineage | Undefined |
| Benchmark independence | Possible but encourages historical shape copying | Generic IDs and explicit configuration | Cannot process new projects | Unproven |
| New-project capability | Only after schema redesign | Yes after builder implementation | No | Not evidenced |

Option B is selected by repository evidence, not preference. Intake Project Spec
already has a stable accepted purpose; Core models and policies already own
methodology; the missing information is project-specific execution/release
configuration.

## ADR-G46-02 - Project Spec schema

**Decision:** do not change `EXPLORA_PROJECT_SPEC_V1` in Gate 46. Intake fields
that are already authoritative are referenced by fingerprint. Executable
structure, metric, request-family and release data belongs in ER.

## ADR-G46-03 - Metrics

**Decision:** MetricSpecs require explicit ER configuration selecting accepted
Core formula identities and complete denominator/missing/weight/parameter
semantics. Question type may constrain compatibility but never selects a metric
by itself.

## ADR-G46-04 - Structures

**Decision:** executable structure semantics are explicit ER records. Project
Spec supplies candidate question/category/source identities. RM selected values,
not-selected values, missing values, completion/storage, denominator scope,
option bindings and applicability cannot be inferred from labels or columns.

## ADR-G46-05 - Requests

**Decision:** ER contains the final one-question request matrix. A Project Spec
output request is presentation/output intent and may name several questions.
No implicit Cartesian expansion or splitting is authorized.

## ADR-G46-06 - Significance

**Decision:** B2 supplies test, version, eligibility and adjustment methodology.
ER supplies explicit project family membership, sample relationship, scope and
references. Project Spec confidence/intent alone is insufficient.

## ADR-G46-07 - Weights

**Decision:** Project Spec weight entries are candidates. ER releases complete
B1-compatible WeightSpecs, default/override scope and explicit unweighted
requests. Missing configuration blocks release.

## ADR-G46-08 - Manifest and release

**Decision:** package/file hashes and inventories are deterministic builder
outputs. Package identity/version and authoritative source artifacts are ER
inputs. `RELEASED`, decision ID and release timestamp are B3 human/release
authority. File presence never implies release.

## ADR-G46-09 - Statistical observations

**Decision:** source counts, observed missing/exclusivity counts, significance
prechecks and execution flags are statistical/runtime evidence. The authoring
layer neither computes nor promotes them to configuration authority. If an old
profile requires them, an accepted external QA artifact must supply them or
authoring fails closed.

## ADR-G46-10 - Physical binding

**Decision:** simple logical-to-source-name joins are deterministic. Any
structure requiring roles/options/axes beyond exact Project Spec identity must
use explicit ER bindings. Similar labels and column naming patterns are never
authority.

## ADR-G46-11 - Packaging determinism

**Decision:** semantic hashes use canonical JSON. A future builder must freeze
ZIP entry order, timestamp and compression before claiming deterministic ZIP
bytes. Until then semantic identity and container identity remain distinct.

## ADR-G46-12 - ATLAS

**Decision:** ATLAS/Pantalones is a read-only future evidence target. Its current
source and metadata do not create generic defaults. It remains blocked pending
an accepted Project Spec, ER configuration and human release decisions.
