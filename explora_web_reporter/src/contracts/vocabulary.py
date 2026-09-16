from __future__ import annotations

from enum import Enum


class CanonicalEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class ReleaseLifecycle(CanonicalEnum):
    PROPOSED = "PROPOSED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RELEASED = "RELEASED"


class ReleaseMode(CanonicalEnum):
    AUTO = "AUTO"
    REVIEW = "REVIEW"
    MANUAL = "MANUAL"


class QAIssueState(CanonicalEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class QAIssueLifecycle(CanonicalEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    WAIVED = "WAIVED"


class StatisticalQAState(CanonicalEnum):
    PASS = "PASS"
    WARN = "WARN"
    INELIGIBLE = "INELIGIBLE"
    UNSUPPORTED = "UNSUPPORTED"
    FAIL = "FAIL"


class StatisticalState(CanonicalEnum):
    SIGNIFICANT = "SIGNIFICANT"
    NOT_SIGNIFICANT = "NOT_SIGNIFICANT"
    INELIGIBLE = "INELIGIBLE"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_TESTED = "NOT_TESTED"
    FAIL = "FAIL"


class AggregateReleaseState(CanonicalEnum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class SampleRelationship(CanonicalEnum):
    INDEPENDENT = "INDEPENDENT"
    PAIRED = "PAIRED"
    REPEATED = "REPEATED"
    PANEL = "PANEL"
    UNKNOWN = "UNKNOWN"


class ExecutionMode(CanonicalEnum):
    LEGACY = "LEGACY"
    CORE_WRAPPER = "CORE_WRAPPER"
    CANONICAL_V1 = "CANONICAL_V1"
    DUAL_RUN = "DUAL_RUN"


class CanonicalBaseMeasure(CanonicalEnum):
    UNWEIGHTED_N = "unweighted_n"
    WEIGHTED_N_RAW = "weighted_n_raw"
    WEIGHTED_N = "weighted_n"
    EFFECTIVE_N = "effective_n"


class StructureAuthorityMode(CanonicalEnum):
    LEGACY_INFERENCE = "legacy_inference"
    RELEASED_SPEC = "released_spec"


class StructureType(CanonicalEnum):
    RU = "RU"
    RM = "RM"
    GRID_ESCALA = "GRID_ESCALA"
    GRID_RM = "GRID_RM"
    LOOP_RM = "LOOP_RM"
    LOOP_RU = "LOOP_RU"
    LOOP_NUMERICO = "LOOP_NUMERICO"


class AxisRole(CanonicalEnum):
    ENTITY = "entity"
    ROW = "row"
    COLUMN = "column"
    OPTION = "option"
    LOOP = "loop"


class StorageEncoding(CanonicalEnum):
    SINGLE_VARIABLE = "single_variable"
    ONE_COLUMN_PER_OPTION = "one_column_per_option"
    LONG_RECORDS = "long_records"


class ResponseStateValue(CanonicalEnum):
    VALID_CATEGORY = "valid_category"
    SELECTED = "selected"
    NOT_SELECTED = "not_selected"
    ANSWERED = "answered"
    NOT_ANSWERED = "not_answered"
    ORDINARY_MISSING = "ordinary_missing"
    STRUCTURAL_MISSING = "structural_missing"
    STRUCTURAL_ZERO = "structural_zero"
    INVALID_OUT_OF_DOMAIN = "invalid_out_of_domain"


class DuplicatePolicy(CanonicalEnum):
    KEEP = "keep"
    DEDUPLICATE_BY_CATEGORY = "deduplicate_by_category"
    ERROR = "error"


class CompletionPolicy(CanonicalEnum):
    EXPLICIT_RESPONSE = "explicit_response"
    MISSING_SET_UNANSWERED = "missing_set_unanswered"


class DenominatorUnit(CanonicalEnum):
    RESPONDENT = "respondent"
    RESPONDENT_OPTION = "respondent_option"
    MENTION = "mention"
    INSTANCE = "instance"


class StructureExecutionStatus(CanonicalEnum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"


class LegacyStructureComparisonStatus(CanonicalEnum):
    PARITY = "PARITY"
    INTENDED_CORRECTION = "INTENDED_CORRECTION"
    POTENTIAL_REGRESSION = "POTENTIAL_REGRESSION"
    UNSUPPORTED = "UNSUPPORTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class ValueStatus(CanonicalEnum):
    OK = "OK"
    NO_VALID_BASE = "NO_VALID_BASE"
    UNSUPPORTED = "UNSUPPORTED"
    INELIGIBLE = "INELIGIBLE"
    ERROR = "ERROR"


class ValueUnit(CanonicalEnum):
    COUNT = "COUNT"
    PROPORTION = "PROPORTION"
    MEAN = "MEAN"
    STANDARD_DEVIATION = "STANDARD_DEVIATION"
    SCORE = "SCORE"


class ComputationStatus(CanonicalEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class QAReleaseStatus(CanonicalEnum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    FAIL = "FAIL"


class QADomain(CanonicalEnum):
    UNIVERSE = "UNIVERSE"
    WEIGHT = "WEIGHT"
    STRUCTURE = "STRUCTURE"
    METRIC = "METRIC"
    STATISTICAL = "STATISTICAL"
    RESULT = "RESULT"
    RELEASE = "RELEASE"


class QAScopeType(CanonicalEnum):
    RESULT = "RESULT"
    REQUEST = "REQUEST"
    SLICE = "SLICE"
    BASE = "BASE"
    VALUE = "VALUE"
    COMPARISON = "COMPARISON"
    UPSTREAM = "UPSTREAM"


class LegacyCanonicalComparisonStatus(CanonicalEnum):
    PARITY = "PARITY"
    INTENDED_CORRECTION = "INTENDED_CORRECTION"
    M2_BASE_DIFFERENCE = "M2_BASE_DIFFERENCE"
    M3_WEIGHT_DIFFERENCE = "M3_WEIGHT_DIFFERENCE"
    M4_STRUCTURE_DIFFERENCE = "M4_STRUCTURE_DIFFERENCE"
    UNSUPPORTED_V1 = "UNSUPPORTED_V1"
    POTENTIAL_REGRESSION = "POTENTIAL_REGRESSION"
    PRESENTATION_ONLY = "PRESENTATION_ONLY"
