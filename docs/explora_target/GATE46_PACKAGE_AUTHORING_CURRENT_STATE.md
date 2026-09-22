# Gate 46 Package Authoring Current State

## Scope and baseline

This audit is contract/readiness only. It starts from official `main`
`c0b5dbb08ffca7425a864f00688e3c9472e0f7df`, after Gate 45 was accepted and
merged through PR #18. No runtime, schema, Core, B1/B2/B3, M2-M7, Legacy, or
statistical behavior is changed.

## Existing path

The accepted productive flow is:

`EXPLORA_PROJECT_SPEC_V1 -> ProjectExecutionBinding -> externally authored
RELEASED ZIP -> materialize_project -> CANONICAL_V1 -> Canonical Results`.

`src/canonical_materialization/materializer.py` declares ten `PACKAGE_FILES`,
requires each file in the ZIP, loads JSON into `ReleasedPackage`, checks manifest
status and execution mode, binds physical variables, and validates selected
references. It does not author any package file. `request.py` narrows a released
request to one question and resolves metric/formula identities. `orchestrator.py`
adapts released dictionaries to the frozen Core contracts.

There is no accepted generic RELEASED-package builder. The only accepted real
package is the externally maintained Benchmark A release. It is evidence of the
current file shape, not a generic authoring template.

## Authority inventory

| Authority | What it currently supplies | Authoring consequence |
|---|---|---|
| `EXPLORA_PROJECT_SPEC_V1` | Project/dataset identity, variables, question intake, universe rules, weight candidates, banner/filter candidates, significance intent, output intent, ambiguities, AI decisions, provenance | Necessary but not sufficient for RELEASED execution configuration. |
| `ProjectExecutionBinding` | Fingerprinted selection of an already accepted spec, source, package and execution identities | It consumes package identity; it cannot create package semantics. |
| Core contract models/validators | Executable `ProjectSpec`, `QuestionSpec`, `StructureSpec`, `UniverseSpec`, `WeightSpec`, `MetricSpec`, `SignificanceSpec`, release guards | Accepted target shapes and policy constraints; no project-specific values may be guessed. |
| B1 | Weight validation, base identities and unsupported behavior | Policy-derived defaults only; weight selection and scope remain explicit. |
| B2 | Tests, versions, eligibility, family rules, Holm and unsupported behavior | Methodology is policy-derived; project family membership and sample relationship require explicit release configuration/approval. |
| B3 | Lifecycle, AI/human boundary, evidence and RELEASED authority | Every executable artifact requires a complete release decision envelope. |
| `load_released_package` | Ten-file presence and JSON loading | Loader compatibility must be preserved. It is not a schema validator or author. |
| `materialize_project` | Physical binding, domain/reference QA and runtime fingerprint | Statistical/source QA produced here remains runtime evidence, not authoring output. |

## Verified gaps

1. Metric definitions are absent from Project Spec. Question type does not
   uniquely select formula, denominator, weight behavior, significance support,
   or parameters.
2. Structure intake lacks complete executable axes/bindings and, especially for
   RM, selected/not-selected/missing semantics, completion/storage policy,
   denominator scope, exclusive behavior and response-state identity.
3. One output request may contain multiple questions/banners/filters, while a
   released request has one `question_ref` plus explicit metrics, universe,
   weight and significance. Splitting is an analytical release decision.
4. Significance intent lacks complete B2 family identity, test/version identity,
   eligibility configuration, member set and sample relationship.
5. Weight candidates do not fully express released scope, overrides, explicit
   unweighted requests and the complete B1 `WeightSpec` release envelope.
6. Release/package identity, version, hashes, timestamp, file manifest and B3
   decision evidence are not Project Spec intake concerns.
7. Project Spec variables and source variables can bind current simple RU cases,
   but cannot prove all RM, grid, loop, scale and applicability semantics.
8. The current Benchmark package contains source-observation snapshots. Those
   values are statistical evidence and cannot be calculated by an authoring
   compiler. They are non-authoritative for the ten-file target contract.

## ATLAS evidence target

Authoritative-looking ATLAS/Pantalones source and metadata artifacts exist
locally and were treated read-only. Existing readiness evidence shows RU, RM,
weights, banners, filters and scale/mean candidates, but no accepted ATLAS
Project Spec, Metric Specs, Structure Specs, request matrix, Significance Specs
or B3 release decision. Therefore ATLAS is a useful future sufficiency target
but is currently blocked for package authoring. No customer raw data is added.

## Current-state conclusion

Project Spec alone is insufficient. Existing accepted contracts provide policy
and target model authority, but they do not contain all project-specific release
choices. A new additive release-input contract is required; implementation is
outside Gate 46.
