from __future__ import annotations

from dataclasses import dataclass
import math

from src.analytics_core.result_identity import make_id
from src.contracts.models import SignificanceRelation, SignificanceSpec
from src.contracts.validators import validate_significance_spec
from src.contracts.vocabulary import SampleRelationship, StatisticalQAState, StatisticalState

ENGINE_VERSION = "B2_CORE_SIGNIFICANCE_V1"


class SignificanceExecutionError(ValueError):
    pass


@dataclass(frozen=True)
class ProportionComparisonInput:
    left_member_id: str
    right_member_id: str
    left_slice_id: str
    right_slice_id: str
    left_numerator: int
    right_numerator: int
    left_unweighted_n: int
    right_unweighted_n: int
    respondent_binary: bool = True
    sample_relationship: SampleRelationship = SampleRelationship.INDEPENDENT
    weighted_inference: bool = False


@dataclass(frozen=True)
class ProportionFamilyRequest:
    spec: SignificanceSpec
    question_id: str
    metric_id: str
    analytical_scope: str
    family_id: str
    comparisons: tuple[ProportionComparisonInput, ...]


def execute_proportion_family(*, spec: SignificanceSpec, result_run_id: str,
                              question_id: str, metric_id: str, analytical_scope: str,
                              family_id: str, comparisons: tuple[ProportionComparisonInput, ...]
                              ) -> tuple[SignificanceRelation, ...]:
    validate_significance_spec(spec)
    for value, name in ((result_run_id, "result_run_id"), (question_id, "question_id"),
                        (metric_id, "metric_id"), (analytical_scope, "analytical_scope"),
                        (family_id, "family_id")):
        if not isinstance(value, str) or not value.strip():
            raise SignificanceExecutionError(f"Missing comparison identity: {name}")
    if not comparisons:
        raise SignificanceExecutionError("Empty comparison family")
    identities = [(item.left_member_id, item.right_member_id, item.left_slice_id, item.right_slice_id)
                  for item in comparisons]
    if len(set(identities)) != len(identities):
        raise SignificanceExecutionError("Duplicate comparison identity")

    evaluated = [_evaluate(item) for item in comparisons]
    eligible = [(index, item[0]) for index, item in enumerate(evaluated) if item[1] is None]
    adjusted = _holm([p for _, p in eligible])
    adjusted_by_index = {index: value for (index, _), value in zip(eligible, adjusted)}
    relations = []
    for index, (item, (raw_p, reason, diagnostics)) in enumerate(zip(comparisons, evaluated)):
        status = StatisticalState.INELIGIBLE if reason and reason.startswith("INELIGIBLE_") else (
            StatisticalState.UNSUPPORTED if reason else
            (StatisticalState.SIGNIFICANT if adjusted_by_index[index] < spec.alpha
             else StatisticalState.NOT_SIGNIFICANT))
        direction = None
        if raw_p is not None:
            left = item.left_numerator / item.left_unweighted_n
            right = item.right_numerator / item.right_unweighted_n
            direction = "LEFT_GREATER" if left > right else "RIGHT_GREATER" if right > left else None
        identity = {"result_run_id": result_run_id, "question_id": question_id,
                    "metric_id": metric_id, "scope": analytical_scope, "family_id": family_id,
                    "left_member_id": item.left_member_id, "right_member_id": item.right_member_id,
                    "left_slice_id": item.left_slice_id, "right_slice_id": item.right_slice_id,
                    "test_id": spec.test_id, "test_version": spec.test_version,
                    "confidence": spec.confidence}
        provenance = (f"engine:{ENGINE_VERSION}", f"policy:{spec.policy_version}",
                      f"reason:{reason or 'ELIGIBLE'}", f"adjustment:{spec.adjustment}:{spec.adjustment_version}",
                      f"diagnostics:{diagnostics}")
        relations.append(SignificanceRelation(
            comparison_id=make_id("comparison", identity), question_id=question_id,
            metric_id=metric_id, analytical_scope=analytical_scope, family_id=family_id,
            left_slice_id=item.left_slice_id, right_slice_id=item.right_slice_id,
            left_member_id=item.left_member_id, right_member_id=item.right_member_id,
            test_id=spec.test_id, test_version=spec.test_version, confidence=spec.confidence,
            status=status, raw_p_value=raw_p, adjusted_p_value=adjusted_by_index.get(index),
            direction=direction, provenance_refs=provenance))
    return tuple(relations)


def _evaluate(item: ProportionComparisonInput):
    for value, name in ((item.left_member_id, "left_member_id"),
                        (item.right_member_id, "right_member_id"),
                        (item.left_slice_id, "left_slice_id"), (item.right_slice_id, "right_slice_id")):
        if not isinstance(value, str) or not value.strip():
            raise SignificanceExecutionError(f"Missing comparison identity: {name}")
    if item.left_member_id == item.right_member_id or item.left_slice_id == item.right_slice_id:
        raise SignificanceExecutionError("Incompatible comparison identity")
    diagnostics = {"left_n": item.left_unweighted_n, "right_n": item.right_unweighted_n,
                   "left_x": item.left_numerator, "right_x": item.right_numerator}
    if item.weighted_inference:
        return None, "UNSUPPORTED_WEIGHTED_INFERENCE", diagnostics
    if item.sample_relationship is not SampleRelationship.INDEPENDENT:
        return None, "UNSUPPORTED_SAMPLE_RELATIONSHIP", diagnostics
    if not item.respondent_binary:
        return None, "UNSUPPORTED_NONBINARY_OUTCOME", diagnostics
    values = (item.left_numerator, item.right_numerator, item.left_unweighted_n, item.right_unweighted_n)
    if any(type(value) is not int or value < 0 for value in values):
        raise SignificanceExecutionError("Invalid count input")
    if item.left_numerator > item.left_unweighted_n or item.right_numerator > item.right_unweighted_n:
        raise SignificanceExecutionError("Numerator exceeds unweighted base")
    if min(item.left_unweighted_n, item.right_unweighted_n) < 30:
        return None, "INELIGIBLE_MINIMUM_BASE", diagnostics
    pooled = (item.left_numerator + item.right_numerator) / (item.left_unweighted_n + item.right_unweighted_n)
    expected = (item.left_unweighted_n * pooled, item.left_unweighted_n * (1-pooled),
                item.right_unweighted_n * pooled, item.right_unweighted_n * (1-pooled))
    diagnostics["pooled"] = pooled
    diagnostics["expected_counts"] = expected
    if min(expected) < 5:
        return None, "INELIGIBLE_EXPECTED_COUNT", diagnostics
    se = math.sqrt(pooled * (1-pooled) * (1/item.left_unweighted_n + 1/item.right_unweighted_n))
    if not math.isfinite(se) or se == 0:
        return None, "INELIGIBLE_DEGENERATE_VARIANCE", diagnostics
    z = (item.left_numerator/item.left_unweighted_n - item.right_numerator/item.right_unweighted_n) / se
    raw = math.erfc(abs(z) / math.sqrt(2))
    diagnostics.update({"standard_error": se, "z": z, "sidedness": "two_sided"})
    return raw, None, diagnostics


def _holm(values: list[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda pair: (pair[1], pair[0]))
    result = [0.0] * len(values)
    previous = 0.0
    for rank, (index, value) in enumerate(ordered):
        previous = max(previous, min(1.0, (len(values) - rank) * value))
        result[index] = previous
    return result
