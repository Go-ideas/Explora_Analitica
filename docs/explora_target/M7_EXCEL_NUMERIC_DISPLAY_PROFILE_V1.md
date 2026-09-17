# M7 Excel Numeric Display Profile V1

Contract ID: M7_EXCEL_NUMERIC_DISPLAY_PROFILE_V1. Status: FROZEN.
This is a storage/display requirement, not an implemented Excel numeric backend.

## Authority and exact storage

canonical_value is the unchanged source scalar plus source unit/status and
canonical record identity. Preserve the complete existing canonical serialized
payload, with checksum and ordered chunks, independently of visible cell storage.
Do not convert a serialized integer to a float or round the analytical payload.
display_value is presentation only; display_format does not change authority.

Two explicitly selected storage modes are supported:
- exact_numeric: finite source scalar, at most 15 significant decimal digits,
  integer magnitude at most 999999999999999, and exact scalar/type-equivalent
  canonical round-trip after workbook readback. No numeric tolerance is allowed.
- exact_text: the exact canonical serialized scalar as a literal text cell,
  visibly identified as exact text; used only when explicitly bound in Visual Spec.

exact_numeric failure aborts publication. There is no automatic conversion to
text, approximate number, zero or blank. Numeric backend certification must test
actual readback; a digit count alone is not proof of exactness. Exact payload is
mandatory in both modes. Non-finite values are rejected under canonical validation.
Negative numbers remain numeric in exact_numeric; text safety is not number parsing.

## Frozen default display profiles

| Source | Numeric storage | Display format |
| --- | --- | --- |
| COUNT integral / unweighted_n | unchanged integer | 0 |
| COUNT fractional | unchanged scalar | 0.00 |
| PROPORTION | unchanged ratio, never divide by 100 | 0.0% |
| MEAN / STANDARD_DEVIATION / SCORE | unchanged scalar | 0.00 |
| weighted_n / weighted_n_raw | unchanged scalar, separate fields | 0.00 |
| Other declared decimal presentation | unchanged scalar | 0.00 |
| effective_n | unchanged scalar in QA only | 0.00 |

A supplied PROPORTION of 0.1234 is stored as 0.1234 and displayed as 12.3%;
a SCORE of 12.34 stays a SCORE, never classified by its label.
weighted_n_raw and weighted_n are not interchangeable. Never derive one from
the other. effective_n is not an official base replacement. A mean/score profile
does not imply that any currently unsupported Core metric has become supported.

Invariant programmatic display text uses decimal dot, no grouping and explicit
percent suffix, rounded half-even from the canonical serialized decimal scalar.
Percent text scaling is presentation only. Excel number formats may use the
viewer's locale/native display rounding; they do not certify analytical precision.
The normalized QA oracle checks stored scalar and format, not localized screen
glyphs. If exact displayed text is required, use an explicitly bound display-text
slot generated with the invariant rule, alongside unchanged authority.
No configurable precision or locale inference in V1; a changed default requires
a versioned contract revision. Exact_text authoritative slots are not reformatted.

## Missing and nonnumeric states

| State | Official visible numeric slot | Audit |
| --- | --- | --- |
| OK with numeric estimate | exact_numeric or explicit exact_text | source retained |
| Null estimate | blank plus NULL annotation | null retained, never zero |
| NO_VALID_BASE / INELIGIBLE / ERROR | blank plus exact source status | QA/release retained |
| UNSUPPORTED | blank plus UNSUPPORTED annotation | source status retained |
| Presentation suppressed | blank plus SUPPRESSED annotation | value retained with authority/reason |
| Required source absent | render fails | MISSING_SOURCE renderer QA |
| Optional source absent | blank plus NOT_COMPUTED annotation | missing binding recorded |

A valid numeric zero is not missing. Null is distinct from absent source.
Suppressed and NOT_COMPUTED are renderer presentation states, not additions to
Core ValueStatus. Unknown source units/statuses fail closed. Workbook blank cells
alone cannot encode these distinctions; status sidecars and CellMap are mandatory.

