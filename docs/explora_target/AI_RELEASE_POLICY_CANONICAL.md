> **EXPLORA — B3 AI Auto-Release Policy — CANONICAL**
> **Version:** V1
> **Date:** 2026-09-14
> **Governance status:** HUMAN APPROVED
> **Authority:** Canonical B3 source for AI-to-Spec release authorization.
> **Scope:** policy only; no code implementation is implied by this approval.
> **Protected authorities:** `WEIGHT_POLICY_CANONICAL.md` (B1) and `SIGNIFICANCE_POLICY_CANONICAL.md` (B2) remain unchanged and authoritative.
> **Progression restriction:** B3 approval does not authorize automatic progression to Gate 1 Final.

# AI_RELEASE_POLICY_CANONICAL

## 1. Canonical principle

**B3-AR-001 — AI proposal is not runtime truth.** EXPLORA NG may interpret, propose and provide evidence. An AI proposal does not become runtime truth because of confidence, persuasive language or mere existence.

**B3-AR-002 — Release policy is mandatory.** Every AI-involved decision must pass B3 release policy before it can become a Project/Question Spec `RELEASED`.

**B3-AR-003 — No silent certainty.** Missing or insufficient evidence can never be converted silently into runtime certainty.

## 2. Official release modes

**B3-AR-010 — AUTO.** A decision may release without human intervention only when all are true: capability permits AUTO; evidence is sufficient; required deterministic rules pass; no blocking conflict flag exists; dependencies are RELEASED; and release QA passes.

**B3-AR-011 — REVIEW.** REVIEW is a blocking pre-release state. A person must accept, reject or modify the proposal before it can become runtime authority.

**B3-AR-012 — MANUAL.** The authoritative value must originate explicitly from a human decision or approved configuration. AI may advise but cannot authorize release.

## 3. Confidence

**B3-AR-020.** V1 has no universal numeric confidence threshold.

**B3-AR-021.** Confidence is a supporting signal, never sufficient authority.

**B3-AR-022.** High confidence cannot override contradiction flags, insufficient evidence, incomplete dependencies, MANUAL capability rules or unsupported structures.

**B3-AR-023.** A calibrated numeric confidence model is deferred. If later approved, it must operate only after deterministic evidence passes and no conflict flags exist; by itself it cannot expand the HIGH/CRITICAL AUTO whitelist.

## 4. Impact and CRITICAL AUTO whitelist

Impact levels are `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.

**B3-AR-030.** HIGH/CRITICAL AUTO requires a specifically approved deterministic profile.

**B3-AR-031.** V1 CRITICAL AUTO whitelist is limited to:
1. exact/authoritative Question↔Variable Mapping;
2. Universe completely explicit and executable;
3. Structural zero/missing completely explicit and validated.

**B3-AR-032.** AI confidence cannot expand this whitelist.

## 5. Question ↔ Variable Mapping

**B3-AR-040.** Default state is `REVIEW`.

**B3-AR-041.** AUTO is permitted only when the variable exists, mapping is unique, exact/authoritative evidence exists, labels/codes/value labels and structure are compatible, no plausible alternative candidate exists, and no questionnaire↔database contradiction exists.

**B3-AR-042.** Any semantic tie-break requires `REVIEW`.

**B3-AR-043.** Exceptional remap outside the supported evidence model is `MANUAL`.

## 6. Question Type / Structure

**B3-AR-050.** Default state is `REVIEW`.

**B3-AR-051.** AUTO requires questionnaire semantics and observed database response semantics to agree under supported deterministic rules.

**B3-AR-052.** Variable-name pattern alone is never sufficient classification evidence.

**B3-AR-053.** RM/Grid ambiguity, mixed encoding, parent ambiguity, missing catalog or inconsistent scale requires `REVIEW`.

**B3-AR-054.** RM/Grid/Loop AUTO additionally requires explicit structure, complete bindings, unique parent, resolved axes, resolved selected/not-selected semantics and resolved applicability.

**B3-AR-055.** A structure outside V1 representation becomes `MANUAL` or `UNSUPPORTED` as appropriate.

## 7. Universe / Base

**B3-AR-060.** Universe is `CRITICAL`; default state is `REVIEW`.

**B3-AR-061.** AUTO is an exception only when the rule comes explicitly from authoritative questionnaire/configuration, converts without loss to the supported Universe Spec/AST, all references exist, all upstream dependencies are RELEASED, the database does not contradict it, and no semantic inference about applicability is required.

**B3-AR-062.** Missing pattern, observed valid N or convenience of available responses never defines an AUTO universe.

**B3-AR-063.** Missing required activation reference routes to `REVIEW / BLOCK`; no observed-response fallback is allowed.

## 8. Structural zero / missing

**B3-AR-070.** Default state is `REVIEW`.

**B3-AR-071.** AUTO is permitted only when applicability and coding are explicit and the observed database confirms rather than defines the semantics.

**B3-AR-072.** Zero/missing frequency patterns alone cannot define structural semantics.

## 9. Weight

**B3-AR-080.** B1 remains the sole weight-methodology authority.

**B3-AR-081.** AI may identify a weight candidate and provide evidence.

**B3-AR-082.** AI cannot productively register a weight, select a default weight or select an analysis override.

**B3-AR-083.** Weight activation is `MANUAL` and must satisfy B1 explicit configuration/validation.

## 10. Metric

**B3-AR-090.** Technical metric compatibility may be determined automatically.

**B3-AR-091.** Primary metric selection may AUTO only when a unique approved/versioned Metric Spec/Registry default determines it.

**B3-AR-092.** When multiple valid metrics exist, selection is `REVIEW`.

**B3-AR-093.** Custom/derived metrics are `MANUAL` unless an approved registry definition uniquely governs them.

**B3-AR-094.** B3 never overrides B2 inferential eligibility.

## 11. Factors / Scores

**B3-AR-100.** Identifying a battery as a factor/score candidate is `REVIEW`.

**B3-AR-101.** Components, formula, direction, reverse coding, weights and cut points are `MANUAL`, unless a previously approved/versioned `formula_id` in the registry uniquely governs the case.

**B3-AR-102.** Methodological examples never become executable formulas automatically.

## 12. Banners and Filters

**B3-AR-110.** Technical banner eligibility may be AUTO when explicit deterministic rules exist.

**B3-AR-111.** Commercial/analytical banner usefulness is `REVIEW`.

**B3-AR-112.** Release as an available banner is `REVIEW` in V1.

**B3-AR-113.** Default banner/comparison selection is `MANUAL / project configuration`.

**B3-AR-114.** No global auto-banner thresholds/profile are approved in V1; future design is deferred.

**B3-AR-115.** Technical filter eligibility may be AUTO.

**B3-AR-116.** Filter recommendation is `REVIEW`.

**B3-AR-117.** Applying a default filter in a project is `MANUAL` in V1; AI never activates a semantic default filter.

**B3-AR-118.** Methodological applicability belongs in Universe Spec and must not be hidden as a commercial filter.

## 13. Visual, order and dashboard exclusion

**B3-AR-120.** Visual recommendation defaults to `AUTO` only when presentation-only and numerically neutral.

**B3-AR-121.** A visual implying aggregation, recode, Top-N analytical suppression, new metric or universe/base change requires `REVIEW` or the corresponding deterministic rule.

**B3-AR-122.** Original questionnaire order plus deterministic parent/child grouping is `AUTO`; editorial/storytelling reorder is `REVIEW / MANUAL` according to project governance.

**B3-AR-123.** IDs, technical variables, helper variables, weight variables as questions and structural children already represented by a parent may be AUTO-excluded from dashboard question lists.

**B3-AR-124.** Excluding analyzable content is `REVIEW`; explicit commercial suppression is `MANUAL / project override`.

## 14. Canonical conflict blockers

**B3-AR-130.** Any blocking conflict invalidates AUTO regardless of confidence.

Canonical blockers include: questionnaire↔database contradiction; ambiguous mapping; multiple plausible parents; ambiguous axis semantics; universe not executable; missing activation reference; unresolved zero/missing semantics; unknown weight authority; unsupported metric/method; required catalog missing; unknown dependency structure when material; unapproved derived formula; conflict with RELEASED upstream Spec; source-version mismatch; semantic-only evidence for HIGH/CRITICAL decisions; blocking QA issue.

## 15. Human override and learning

**B3-AR-140.** Human overrides are project-scoped, versioned, auditable and require a reason.

**B3-AR-141.** Project correction does not modify global rules automatically.

**B3-AR-142.** Repeated correction lifecycle is: observed pattern → candidate rule → methodological review → approval → versioned deterministic rule → tests/regression.

**B3-AR-143.** Repeated correction never becomes automatic global learning.

## 16. Failure policy

**B3-AR-150.** `BLOCK`: a required critical decision/dependency cannot proceed.

**B3-AR-151.** `REVIEW`: evidence supports a candidate but human validation is required.

**B3-AR-152.** `UNSUPPORTED`: capability/method is outside approved support; no fallback under the same semantic label.

**B3-AR-153.** `NOT_AVAILABLE`: required source/evidence does not exist or cannot be evaluated; this is not false, zero, missing response or no filter.

**B3-AR-154.** No silent permissive fallback is allowed.

## 17. Release lifecycle

**B3-AR-160.** Required lifecycle states are:
- `PROPOSED`;
- `REVIEW_REQUIRED`;
- `APPROVED`;
- `REJECTED`;
- `RELEASED`.

**B3-AR-161.** Only `RELEASED` may be consumed by Analytics Core as runtime authority.

**B3-AR-162.** AUTO or human review may authorize release only when the applicable policy and QA requirements pass.

**B3-AR-163.** Prior states/values and version lineage remain auditable when a released decision is replaced.

## 18. Audit trail

**B3-AR-170.** Every RELEASED decision retains at minimum: capability; proposed/effective value; evidence; source versions; rule version; AI model/version when applicable; release mode; reviewer when applicable; reason; timestamps; prior state/version; conflict status; QA status.

## 19. AI / Spec QA

**B3-AR-180.** Before RELEASED, validate schema, required evidence, deterministic support, conflicts, dependencies, release mode, unresolved review, unsupported status and audit completeness.

**B3-AR-181.** An unresolved CRITICAL review blocks Spec release.

**B3-AR-182.** A Spec containing an unresolved required CRITICAL decision cannot reach Analytics Core as released authority.

## 20. Deferred — approved deferrals

The following are explicitly deferred and do not block B3 closure:

- universal numeric confidence threshold;
- calibrated confidence model;
- global auto-banner thresholds/profile;
- reviewer UI implementation;
- physical persistence implementation;
- final field names after schema freeze;
- automatic learning from review history.

## 21. B3 closure

B3 policy requirements are defined and HUMAN APPROVED. B3 is **PASS** and methodologically closed for V1.

This PASS does not mean implementation exists. It does not authorize code changes, EXPLORA NG changes, EXPLORA Web changes, EXPLORA Excel build, or automatic progression to Gate 1 Final.
