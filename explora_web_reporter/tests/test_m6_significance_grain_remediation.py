from __future__ import annotations

from dataclasses import replace

from src.contracts.models import SignificanceRelation
from src.contracts.vocabulary import StatisticalState
from src.web_canonical.adapter import project_canonical_result
from m6_fixtures import canonical_result


def _relation(**overrides) -> SignificanceRelation:
    payload = {
        "comparison_id": "comparison_metric_1",
        "question_id": "Q1",
        "metric_id": "metric_1",
        "analytical_scope": "banner",
        "family_id": "family_1",
        "left_slice_id": "slice_banner_a",
        "right_slice_id": "slice_banner_b",
        "test_id": "test_1",
        "test_version": "B2_V1",
        "confidence": 0.95,
        "status": StatisticalState.SIGNIFICANT,
    }
    payload.update(overrides)
    return SignificanceRelation(**payload)


def _result_with_values(*, relation: SignificanceRelation):
    result = canonical_result()
    base_a = replace(
        result.bases[0],
        base_id="base_a",
        slice_id="slice_banner_a",
    )
    metric_1 = replace(
        result.values[0],
        value_id="value_metric_1",
        base_id="base_a",
        slice_id="slice_banner_a",
        metric_id="metric_1",
        significance_refs=(relation.comparison_id,),
    )
    metric_2 = replace(
        metric_1,
        value_id="value_metric_2",
        metric_id="metric_2",
        significance_refs=(),
    )
    return replace(
        result,
        bases=(base_a,),
        values=(metric_1, metric_2),
        comparisons=(relation,),
    )


def test_significance_tokens_do_not_leak_across_metrics() -> None:
    projection = project_canonical_result(
        _result_with_values(relation=_relation())
    )
    by_metric = {cell.metric_id: cell.significance_tokens for cell in projection.cells}
    assert by_metric["metric_1"]
    assert by_metric["metric_2"] == ()


def test_significance_tokens_do_not_leak_across_questions() -> None:
    projection = project_canonical_result(
        _result_with_values(relation=_relation(question_id="Q2"))
    )
    assert projection.cells[0].significance_tokens == ()


def test_significance_tokens_do_not_leak_across_family_or_scope() -> None:
    relation = _relation(
        comparison_id="comparison_other_family",
        family_id="family_2",
        analytical_scope="different_scope",
    )
    result = _result_with_values(relation=relation)
    value = replace(
        result.values[0],
        significance_refs=("comparison_metric_1",),
    )
    projection = project_canonical_result(replace(result, values=(value,)))
    assert projection.cells[0].significance_tokens == ()


def test_pairwise_tokens_still_attach_within_same_grain() -> None:
    projection = project_canonical_result(
        _result_with_values(relation=_relation())
    )
    assert projection.cells[0].significance_tokens == ("B",)
