# M7 Dynamic Region Contract V1

Contract ID: `M7_DYNAMIC_REGION_CONTRACT_V1`. Status: NORMATIVE FOR REVIEW.
Gate: 40A contract clarification. Runtime implementation: NOT AUTHORIZED.
Authoritative parent: `833bd04de4e3ccc98a4a39e68f421ae137dceeb8`.

## 1. Purpose And Authority

This contract defines generic, bounded dynamic presentation regions for a future
M7 renderer implementation. A Dynamic Region changes presentation footprint only.
It never creates or changes analytical results.

Analytical authority remains:

`EXPLORA Core -> Canonical Results -> Excel Renderer -> workbook`

Only eligible Canonical Results may supply values, bases, statuses, slices and
significance. A Dynamic Region MUST NOT aggregate respondent data, create slices,
derive percentages, recompute bases, repair weights, calculate means, infer
significance or otherwise replace Core authority.

The keywords MUST, MUST NOT, REQUIRED, SHOULD and MAY are normative.

## 2. Versioning And Compatibility

This is a new additive contract. It does not change the meaning of the frozen:

- `M7_VISUAL_SPEC_V1`;
- `M7_MASTER_INTERFACE_CONTRACT_V1`;
- `M7_CANONICAL_TO_WORKBOOK_MAPPING_V1`;
- `M7_EXCEL_NUMERIC_DISPLAY_PROFILE_V1`;
- `M7_SIGNIFICANCE_PRESENTATION_INTERFACE_V1`.

A future growth-capable runtime MUST explicitly declare this contract ID in its
Master qualification, Visual Spec extension and RenderPlan version. A V1 Visual
Spec without a Dynamic Region extension retains fixed-slot semantics. Existing
Gate 38 and Gate 39 workbooks and requests remain valid fixed-target inputs.

Compatibility requires preservation of numeric display, significance transport,
literal safety, VBA, provenance and deterministic-rendering guarantees. Dynamic
Region fields MUST NOT be silently accepted by an older runtime.

## 3. Normative Vocabulary

### 3.1 Region identity

Each region has a nonempty, stable `region_id`, unique within one qualified
Master interface version. Identity is the tuple:

`master_id, master_version, region_contract_version, region_id`.

The declaration binds `region_id` to a semantic `role_id`, worksheet role and
exact physical binding. Labels, question text, brand text, benchmark identifiers,
workbook scanning and coordinate heuristics MUST NOT establish identity.

### 3.2 Region kinds

`region_kind` is exactly one of:

- `TABLE`: an existing controlled Excel Table/ListObject whose body and footprint
  may be resized inside its owned envelope;
- `RANGE`: a rectangular renderer-owned cell region resolved from a controlled
  named anchor and bounded envelope.

Missing or unknown kinds fail closed.

### 3.3 Growth dimensions

`growth_dimensions` is exactly one of `ROWS`, `COLUMNS`, or
`ROWS_AND_COLUMNS`. The requested logical extent MUST alter only authorized
dimensions. A non-authorized dimension MUST remain at its declared minimum.

Worksheet row insertion, row deletion, column insertion and column deletion are
NOT AUTHORIZED in V1. No operation may shift unrelated workbook structures.

## 4. Master Dynamic Region Declaration

A future Master interface extension MUST expose this logical schema:

```text
DynamicRegionDeclaration
  region_id: nonempty stable string
  region_contract_version: M7_DYNAMIC_REGION_CONTRACT_V1
  role_id: declared Master role
  worksheet_role: declared worksheet semantic role
  region_kind: TABLE | RANGE
  binding:
    table_id: required only for TABLE
    anchor_name: required only for RANGE
  growth_dimensions: ROWS | COLUMNS | ROWS_AND_COLUMNS
  min_rows: positive integer
  min_columns: positive integer
  max_rows: positive integer >= min_rows
  max_columns: positive integer >= min_columns
  owned_envelope: exact top/left/bottom/right bounds resolved from controlled identity
  ownership: RENDERER_OWNED
  field_columns: ordered typed field-to-offset declarations
  style_policy_ref: released DynamicRegionStylePolicy identity
  formula_policy_ref: released DynamicRegionFormulaPolicy identity or NONE
  cleanup_policy: REPLACE_AND_CLEAR_STALE
  collision_policy_ref: M7_DYNAMIC_REGION_COLLISION_V1
  update_policy: REPLACE
```

For `TABLE`, `table_id` MUST identify exactly one existing controlled table and
the owned envelope MUST contain every permitted before/after table footprint.
For `RANGE`, `anchor_name` MUST resolve to exactly one cell in the declared
worksheet role. The envelope is computed from the anchor and declared maxima.

The physical origin, minimum footprint and maximum footprint MUST resolve before
planning. Overflow, unresolved bindings, duplicate IDs, mismatched roles,
non-positive extents and an envelope outside the worksheet fail closed.

The existing audit capacity of 256 records per role remains an independent,
bounded diagnostic transport limit. It is not a Dynamic Region declaration and
is not enlarged or reinterpreted by this contract.

## 5. Visual Spec Extension

A future versioned extension MUST reference regions explicitly:

```text
DynamicRegionBinding
  region_id: declared region identity
  result_run_id: eligible Canonical Result run
  record_role: value | base | slice | comparison | qa | provenance
  ordered_record_ids: explicit ordered canonical record identities
  field_bindings: ordered source-field to declared region-field mappings
  requested_rows: positive integer
  requested_columns: positive integer
  display_profile_refs: exact released profile identities per field
  significance_presentation_refs: checksum-pinned envelopes when applicable
```

`ordered_record_ids` MUST be explicit. Wildcards, label matching, worksheet
content discovery and implicit source selection are prohibited. Requested extent
MUST equal the deterministic extent implied by the ordered bindings. Missing,
negative, zero, non-integer, contradictory or excess cardinality fails closed.

## 6. Ownership And Protected Content

Only cells inside the resolved owned envelope may be classified
`RENDERER_OWNED`. The logical footprint is the active subset for one render; the
remaining cells in the owned envelope are stale-cleanup candidates only.

The following remain protected unless a future separate contract authorizes them:

- VBA, charts, shapes, controls, slicers and pivots;
- Master-owned formulas and names;
- non-owned tables and defined names;
- user-owned content;
- fixed writable slots outside the region;
- cells outside the owned envelope;
- unknown or ambiguous structures.

Ownership MUST be established by released declarations before planning. Unknown,
overlapping or ambiguous ownership fails closed. No last-write-wins behavior is
permitted.

## 7. Formatting And Style Policy

Each region MUST reference one released `DynamicRegionStylePolicy`:

```text
DynamicRegionStylePolicy
  style_policy_id: stable versioned identity
  region_id: owning region
  template_sources: explicit row, column or cell template identities
  propagation_axis: ROWS | COLUMNS | ROWS_AND_COLUMNS
  owned_attributes: explicit subset of font, fill, border, alignment,
                    number_format, protection, row_height, column_width,
                    conditional_formatting
  unsupported_attributes: explicit list
  table_style_policy: PRESERVE_EXISTING_TABLE_STYLE | NOT_APPLICABLE
```

Formatting MUST be copied only from declared template sources, never inferred
from arbitrary neighbors. Every owned attribute MUST have one deterministic
source and propagation rule. Unowned attributes remain byte/logically preserved.
An applicable attribute that is neither owned nor explicitly unsupported fails
closed. TABLE resizing MUST preserve table identity, columns, metadata, style and
references. RANGE propagation MUST preserve the declared style identity exactly.

## 8. Formula Policy

Analytical Excel formulas remain prohibited. The default formula policy is
`NONE`, under which any formula in a projected mutable or stale-clear cell blocks
the plan.

A non-`NONE` `DynamicRegionFormulaPolicy` MUST declare:

```text
DynamicRegionFormulaPolicy
  formula_policy_id: stable versioned identity
  region_id: owning region
  classification: PRESENTATION_ONLY
  source_formula_cells: exact controlled Master identities
  target_field_offsets: exact destinations inside the region
  propagation_axis: authorized region dimension
  normalized_formula_rule: deterministic relative-reference rule
  expected_inventory_rule: exact before/after inventory oracle
```

Propagation is allowed only when the formula already belongs to the controlled
Master, is `PRESENTATION_ONLY`, is explicitly allowlisted, and output validation
proves the expected inventory. Unknown, analytical, unclassified or
non-allowlisted formulas fail closed.

## 9. Collision Policy

Planning MUST calculate complete projected footprints before mutation, including
active writes, table before/after bounds, stale-clear cells, style propagation
and allowlisted formula propagation. The collision validator MUST compare every
projected footprint against:

- every other Dynamic Region envelope and projected footprint;
- fixed writable slots and neighboring renderer targets;
- owned and non-owned Excel Tables;
- defined names whose referents intersect the footprint;
- merged cells;
- formulas not explicitly allowed by the region formula policy;
- nonempty user-owned or Master-owned cells;
- charts, pivots, slicers, controls, shapes and relationships whose preservation
  cannot be demonstrated;
- worksheet and package structures outside declared ownership.

Any overlap requires explicit compatible shared ownership in a future contract;
V1 defines no shared ownership. Therefore every overlap or ambiguity fails
closed before staged output is created.

## 10. Replacement, Contraction And Stale Cleanup

Dynamic Regions use replacement semantics. For each render, the planner derives:

- `before_bounds`: the qualified current active footprint;
- `after_bounds`: the requested logical footprint;
- `owned_envelope`: the immutable maximum boundary;
- `stale_footprint`: renderer-owned cells in `before_bounds - after_bounds`.

The plan MUST clear every stale analytical/presentation value and status inside
the stale footprint. It MUST NOT clear template cells required by the style or
formula policy, nor any Master/user-owned content. TABLE regions resize the table
to `after_bounds`; RANGE regions retain their declared envelope and clear stale
owned cells. A smaller render MUST leave no visible prior-run value, base, status
or significance marker.

The input workbook for an update MUST itself be validated as an output of the
same Master/region contract lineage, or the render MUST start from the controlled
Master. Unverifiable prior extent or cleanup failure fails closed.

## 11. RenderPlan Dynamic Operations

A growth-capable plan MUST use a new explicit plan version and include an ordered
`dynamic_operations` collection. Cell writes alone are insufficient.

```text
DynamicRegionOperation
  operation_id: deterministic identity
  operation_type: VALIDATE_REGION | RESIZE_TABLE | CLEAR_OWNED_STALE |
                  PROPAGATE_STYLE | PROPAGATE_PRESENTATION_FORMULA | WRITE_CELL
  region_id: declared region identity
  result_run_id: canonical source run
  source_record_ids: ordered canonical identities
  before_bounds: exact rectangle
  after_bounds: exact rectangle
  requested_rows: positive integer
  requested_columns: positive integer
  owned_envelope: exact rectangle
  affected_cells: deterministic ordered set or normalized range list
  policy_refs: region/style/formula/collision contract identities
  collision_validation: PASS plus deterministic evidence hash
```

Required operation order is validation, resize when applicable, stale clear,
style propagation, allowlisted presentation-formula propagation, then writes.
Operations of the same type are ordered by `region_id`, canonical semantic order,
source record identity and field offset. The renderer MUST NOT execute a mutation
absent from the accepted plan. Unsupported operation types fail closed.

Every operation and the complete normalized plan MUST be fingerprinted. The plan
records both requested logical extent and actual owned footprint.

## 12. Determinism And Provenance

Identical eligible Canonical Results, ordered bindings, Visual Spec, Dynamic
Region declarations/policies, qualified Master and renderer build MUST produce
an identical normalized RenderPlan and logical workbook state. Ordering MUST NOT
depend on dictionary iteration, labels, incidental blank cells or scanning.

Provenance MUST record:

- Master ID, version and hash;
- Dynamic Region contract and declaration checksums;
- region IDs, before/after bounds and requested extents;
- style, formula and collision policy identities;
- source result/run fingerprints and ordered record IDs;
- operation IDs and normalized plan hash;
- rendered output identity and normalized structural diff;
- preserved VBA and protected-part hashes.

Binary identity is preferred but MUST be claimed only when demonstrated. Any
normalized oracle MUST enumerate excluded volatile package fields and MUST NOT
exclude analytical data, presentation values, operations or contract identities.

## 13. Fail-Closed Requirements

Planning MUST fail before mutation for at least:

- overflow beyond the owned envelope;
- ambiguous or unknown ownership;
- duplicate region or operation identity;
- missing declaration, anchor, table, policy or source identity;
- growth in an unauthorized dimension;
- malformed or contradictory cardinality;
- collision with protected or undeclared content;
- unsupported structural operation or global row/column insertion;
- incompatible source type or numeric display profile;
- stale-cleanup uncertainty or residue;
- unauthorized formula/style propagation;
- significance without canonical authority;
- wrong Master/contract version or hash;
- VBA or protected-package mutation;
- corrupted XLSM/OOXML.

Failure MUST discard staged output. A partial workbook MUST NOT be published or
classified as successful.

## 14. Significance And Numeric Preservation

Dynamic significance markers require canonical `SignificanceRelation`, a valid
checksum-pinned presentation envelope and a Dynamic Region binding to the exact
canonical value/slice/member identity. Contraction MUST clear markers belonging
to removed rows. Values and bases without canonical significance MUST NOT cause
marker reconstruction.

Every dynamic numeric field retains the existing numeric display profile and
storage mode. Growth MUST NOT change canonical scalar, unit, status, precision,
rounding, null behavior or base semantics.

## 15. Explicitly Unsupported In V1

V1 does not authorize dynamic charts, chart movement, pivots, slicers, shapes,
controls, connections, signed packages, worksheet-wide insertion/deletion,
study-specific VBA or Python rules, statistical computation in Excel, changes to
B1/B2/B3, changes to Canonical Result analytical semantics, Legacy fallback,
Web changes, or Welch/mean significance.

## 16. Future Runtime Boundary

Future implementation requires separately reviewed runtime representations for
`DynamicRegionDeclaration`, `DynamicRegionBinding`, style/formula policies and
`DynamicRegionOperation`, plus Master  qualification, validators, RenderPlan
versioning, renderer execution, structural output validation and fixtures.

This document does not implement those objects and does not authorize workbook
resizing. Implementation requires a separate human gate.

## 17. Gate 40A Decision Matrix

| Required question | Normative answer |
| --- | --- |
| Unique identity | Section 3.1 tuple and stable `region_id` |
| Physical anchor | Section 4 exact table ID or named anchor |
| Growth dimensions | Section 3.3 explicit enum |
| Maximum bounds | Section 4 finite owned envelope and maxima |
| Renderer ownership | Section 6 explicit `RENDERER_OWNED` cells only |
| Protected content | Section 6 protected inventory |
| Style inheritance | Section 7 released deterministic policy |
| Formula behavior | Section 8 default NONE or allowlisted presentation-only policy |
| Collision detection | Section 9 projected-footprint validation |
| Smaller result | Section 10 replacement and stale clearing |
| RenderPlan mutations | Section 11 explicit ordered operations |
| Determinism | Section 12 normalized identity and ordering |
| Overflow | Section 13 fail closed before mutation |
| Ambiguous ownership | Sections 6 and 13 fail closed |
| Unsupported scope | Section 15 explicit exclusions |

Contract gap disposition: RESOLVED NORMATIVELY FOR HUMAN REVIEW.
Dynamic runtime implementation: NOT AUTHORIZED.

## 18. Human Decision Traceability

| Decision | Contract disposition |
| --- | --- |
| G40-HR-01 | Section 3.1 defines stable semantic region identity |
| G40-HR-02 | Section 3.2 defines TABLE and RANGE kinds |
| G40-HR-03 | Section 3.3 defines explicit growth dimensions |
| G40-HR-04 | Section 4 defines finite minima, maxima and owned envelope |
| G40-HR-05 | Section 3.3 prohibits worksheet row/column insertion and deletion |
| G40-HR-06 | Section 6 defines renderer ownership and protected content |
| G40-HR-07 | Section 7 defines deterministic formatting inheritance |
| G40-HR-08 | Section 8 defines allowlisted presentation-only formula policy |
| G40-HR-09 | Section 9 defines projected-footprint collision validation |
| G40-HR-10 | Section 10 defines replacement, contraction and stale cleanup |
| G40-HR-11 | Section 11 defines explicit Dynamic Region plan operations |
| G40-HR-12 | Section 12 defines deterministic ordering and output identity |
| G40-HR-13 | Sections 1 and 14 preserve canonical analytical authority |
| G40-HR-14 | Section 2 establishes additive versioning and compatibility |
| G40-HR-15 | Section 15 preserves the explicit out-of-scope boundary |

## 19. Gate 40A Validation

Documentation-focused validation on the authoritative parent completed with:

- M7B + Gate 38 + Gate 39 relevant suites: 141 passed, 0 failed, 0 skipped;
- full regression: 814 passed, 0 failed, 0 skipped;
- unexpected numerical deltas: none detected;
- source, tests, Master and runtime files modified: none.

These results demonstrate non-regression only. They do not constitute Dynamic
Region runtime qualification or implementation authorization.
