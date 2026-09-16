# Productive Benchmark Readiness

Date: 2026-09-15

Status: preparation/evidence only. No M2, M3, M4, M5, M6, B1, B2, B3,
Legacy analytical source, Web implementation, SQLite schema, Excel, or M7
changes were made.

## Candidate Inventory

| Candidate | Path | SHA-256 | Classification | Notes |
|---|---|---:|---|---|
| web_main | `explora_web_reporter/data/db/BD_Analitica_Explora.db` | `1B0BD28180844EBC3CA59A1467B78EE6D486DB6CB8CC71E3D16B3388B77174DB` | PRODUCTIVE_CANDIDATE | Real ATLAS/Pantalones analytical DB shape; raw SPSS/datamap references exist in `explora_web_reporter/data/raw/`. Productive status still requires human/project confirmation. |
| pantalones_test | `TEST/Pantalones/BD_Analitica_Explora.db` | `DFE04264CA0EA2A4A6149A7426C73950B0B10FC903075DE6475EF38DE1AC66A9` | TEST_FIXTURE | Same project family and real-looking files, but under `TEST/`; not selectable as productive without explicit human evidence. |
| session_41933 | `explora_web_reporter/data/sessions/41933cb11ff84b3494d5e2824fc08987/db/BD_Analitica_Explora.db` | `DFE04264CA0EA2A4A6149A7426C73950B0B10FC903075DE6475EF38DE1AC66A9` | DUPLICATE / SESSION_COPY | Byte-identical duplicate of `pantalones_test`. |
| session_957c | `explora_web_reporter/data/sessions/957c9396c774432c80992884c1d761ab/db/BD_Analitica_Explora.db` | `4C77D7AD09D710BCE02312D6C6D6E1C3121115FB06DEF2C599351A4EC209F11D` | SESSION_COPY / UNKNOWN_PROVENANCE | Session DB with partial ATLAS-like metadata. Not counted as separate productive benchmark without provenance approval. |
| gpt_test_bd | `GPT/Test/Documentos/BD.db` | `2DB9D73E98E851284FA63F7F0FD4A0F668D6C0E8E9ACE848310CD3EDD9B2EA42` | TEST_FIXTURE | GPT test schema (`BD_P`, `CAT_*`), not current Explora analytical DB schema. |

## Non-Duplicate Coverage

| Candidate | Respondents | Questions | RU | RM | GRID_ESCALA | GRID_RM | LOOP_RU | LOOP_RM | LOOP_NUMERICO | Weights | Banners | Filters | Significance-Compatible |
|---|---:|---:|---|---|---|---|---|---|---|---|---|---|---|
| web_main | 1,420 | 75 | YES: 24 frequency questions | YES: 17 RM questions; `multirrespuesta_long` has 381 rows | NO explicit grid table/spec evidence | NO | NO | NO | NO | YES: `Pond_MN_Lee`, `Pond_MN_Wrangler` | YES: 28 configured banner rows | YES: 21 configured filter rows | Candidate only: unweighted RU/RM banner cases require B2 SignificanceSpec release |
| pantalones_test | 1,420 | 132 | YES: frequency questions | Metadata/question-family present, but `multirrespuesta_long` has 0 rows | NO explicit grid table/spec evidence | NO | NO | NO | NO | YES: `Pond_MN_Lee`, `Pond_MN_Wrangler` | Metadata available; config has no `banner` rows | Metadata available; config has no `filtro` rows | Candidate only; not productive without human evidence |
| session_957c | 1,420 | 75 | YES: frequency questions | Metadata partial; `multirrespuesta_long` has 0 rows | NO explicit grid table/spec evidence | NO | NO | NO | NO | YES: `Pond_MN_Lee`, `Pond_MN_Wrangler` | NO configured banner rows | YES: 7 configured filter rows | Candidate only; provenance unknown |
| gpt_test_bd | n/a | n/a | UNKNOWN under current schema | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

## Benchmark Recommendations

Benchmark A recommendation:

- `web_main`
- Internal identity: ATLAS/Pantalones candidate, inferred only from metadata and file names.
- Dataset: `explora_web_reporter/data/db/BD_Analitica_Explora.db`
- Supporting references: `explora_web_reporter/data/raw/Atlas_2026_17_02_19_46 Final POND.sav`, `explora_web_reporter/data/raw/Datamap_Validado_ATLAS_2026_WEB_REPORTER.xlsx`, related ATLAS datamap revisions.

Benchmark A coverage:

- RU: YES, e.g. `C4`, `F2`, `F3`, `G1`, `HC2`, `MC1`.
- RM respondent: YES, e.g. `C1B`, `C2`, `C3`, `HC9`, `MC4`.
- RM mention: YES as candidate from RM output; requires MetricSpec for mention denominator.
- Scale/mean: YES, `C7`.
- Weights: YES, `Pond_MN_Lee`, `Pond_MN_Wrangler`.
- Banners: YES, e.g. `C4`, `F2`, `F3r`, `F4`, `Segmento`.
- Filters: YES, e.g. `C3_45`, `C3_82`, `F2`, `F3r`, `F4`, `F5`.
- Supported significance: candidate only; no project-specific SignificanceSpec release found.
- Grid/Loop: NO real explicit metadata/table/spec evidence found.

Benchmark B recommendation:

- No Benchmark B selected.
- Reason: no non-duplicate candidate contains explicit real GRID/LOOP tables/specs sufficient to prepare a productive Grid/Loop benchmark.

## Existing Released Specs And Canonical Results

Search result:

- Existing released Project Specs: NONE FOUND.
- Existing released Question Specs: NONE FOUND.
- Existing released Structure Specs: NONE FOUND.
- Existing released Universe Specs / refs: NONE FOUND.
- Existing released Weight Specs / refs: NONE FOUND.
- Existing released Metric Specs: NONE FOUND.
- Existing project-specific Significance Specs: NONE FOUND.
- Existing productive CanonicalResult artifacts: NONE FOUND.
- Existing request snapshots/result_run_id/result_fingerprint serialized artifacts: NONE FOUND outside test fixtures and implementation docs.

Methodology documents M1-M6 and B1/B2/B3 exist, but they are methodology
authority, not project-specific released configuration for ATLAS/Pantalones.

## Benchmark A Readiness Matrix

| Requirement | Status |
|---|---|
| Dataset available | YES |
| Questionnaire/datamap available | YES: SPSS and datamap references available; questionnaire not found for `web_main` path |
| Project Spec available / released | NO / NO |
| Question Specs available / released | NO / NO |
| Structure Specs available / released | NO / NO |
| Universe Specs available / released | NO / NO |
| Weight Specs available / released / N/A | NO / NO |
| Metric Specs available / released | NO / NO |
| Canonical request ready | NO |
| CanonicalResult exists | NO |
| DUAL_RUN ready | NO |

## Benchmark B Readiness Matrix

| Requirement | Status |
|---|---|
| Dataset available | NO selected real Grid/Loop dataset |
| Questionnaire/datamap available | NO selected real Grid/Loop package |
| Project Spec available / released | NO / NO |
| Question Specs available / released | NO / NO |
| Structure Specs available / released | NO / NO |
| Universe Specs available / released | NO / NO |
| Weight Specs available / released / N/A | NO / NO |
| Metric Specs available / released | NO / NO |
| Canonical request ready | NO |
| CanonicalResult exists | NO |
| DUAL_RUN ready | NO |

## Missing Artifacts - Benchmark A

Minimum project-specific artifacts needed before productive CanonicalResult generation:

- Project Spec for ATLAS/Pantalones candidate, including project_id, dataset fingerprint, respondent ID binding, project universe ref, and default weight policy.
- Question Spec for RU request candidate `C4`.
- Question Spec for RM request candidate `C1B` and/or `C2`.
- Question Spec for scale/mean request candidate `C7`.
- Question Specs for selected banner/filter variables used as analytical slice dimensions, e.g. `F2`, `F3r`, `F4`, `Segmento`, `C3_45`, `C3_82`.
- Structure Spec for `C4` RU.
- Structure Spec for `C1B`/`C2` RM, including selected values, not-selected semantics, duplicate policy, ordinary missing values, and respondent/mention denominator scope.
- Structure Spec for `C7` scale/mean.
- Universe Spec/ref for project universe.
- Universe Spec/ref for each selected question or scope whose applicability is not identical to project universe.
- Universe Spec/ref for filter/banner scope if required by the released request.
- Weight Spec for `Pond_MN_Lee`.
- Weight Spec for `Pond_MN_Wrangler`.
- Metric Specs for RU count/proportion.
- Metric Specs for RM respondent count/proportion.
- Metric Specs for RM mention count/proportion.
- Metric Specs for scale mean/standard deviation where selected.
- SignificanceSpec for supported unweighted banner inference if included.
- Canonical RequestSnapshot for each selected request.
- Generated and validated CanonicalResult for each selected request.

Human input required before release:

- Confirm whether `web_main` is a real productive project benchmark.
- Confirm project identity and allowed internal name.
- Confirm authoritative questionnaire/datamap revision.
- Confirm selected request matrix.
- Confirm universe/applicability rules for `C4`, `C1B`, `C2`, `C7`, and selected filters.
- Confirm RM respondent vs mention denominator semantics.
- Confirm weight authority: `Pond_MN_Lee`, `Pond_MN_Wrangler`, or both.
- Confirm B2 significance scope to include or mark unsupported.

## Missing Artifacts - Benchmark B

- Real productive Grid/Loop dataset or project package.
- Questionnaire/datamap source proving GRID/LOOP structure.
- Released Project Spec.
- Released Question Specs for selected Grid/Loop questions.
- Released Structure Specs for GRID_ESCALA, GRID_RM, LOOP_RU, LOOP_RM, and/or LOOP_NUMERICO.
- Released Universe refs/specs for project, question, row/entity, column/option, loop instance, and applicability where required.
- Released Metric Specs for selected Grid/Loop metrics.
- Released Weight Specs if weighted Grid/Loop validation is required.
- Canonical RequestSnapshots.
- Generated and validated CanonicalResults.

## Canonical Result Generation Plan

For Benchmark A:

1. Freeze dataset and source references.
2. Human-confirm productive benchmark identity and authoritative datamap/questionnaire revision.
3. Release Project Spec.
4. Release selected Question Specs.
5. Release selected Structure Specs.
6. Release Universe refs/specs.
7. Release Weight Specs for selected weight variables, or mark weight N/A for unweighted requests.
8. Release Metric Specs.
9. Create canonical requests for the selected request matrix.
10. Execute CANONICAL_V1 through the existing frozen Core path.
11. Validate CanonicalResult objects.
12. Execute M6 DUAL_RUN with the same normalized analytical requests.

For Benchmark B:

1. Obtain a real Grid/Loop productive project package.
2. Repeat the same freeze/release/generate/validate/DUAL_RUN sequence.

## DUAL_RUN Readiness

DUAL_RUN is not ready for productive validation because the canonical side is
missing project-specific released specs and productive CanonicalResult artifacts.
This is configuration/evidence readiness, not an M2-M6 code defect.
