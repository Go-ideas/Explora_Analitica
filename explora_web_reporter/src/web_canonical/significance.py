from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.contracts.models import (
    CanonicalSlice,
    CanonicalValue,
    SignificanceRelation,
)
from src.contracts.vocabulary import StatisticalState


SIGNIFICANT_STATES = {
    StatisticalState.SIGNIFICANT.value,
    "TESTED_SIGNIFICANT",
}


@dataclass(frozen=True)
class SignificancePresentation:
    tokens_by_slice_id: dict[str, tuple[str, ...]] = field(
        default_factory=dict
    )
    tokens_by_value_id: dict[str, tuple[str, ...]] = field(
        default_factory=dict
    )
    tokens_by_comparison_slice: dict[
        tuple[str, str], tuple[str, ...]
    ] = field(default_factory=dict)
    relations_by_id: dict[str, SignificanceRelation] = field(
        default_factory=dict
    )
    legend: pd.DataFrame = field(default_factory=pd.DataFrame)
    table: pd.DataFrame = field(default_factory=pd.DataFrame)

    def tokens_for_value(self, value: CanonicalValue) -> tuple[str, ...]:
        direct = self.tokens_by_value_id.get(value.value_id)
        if direct is not None:
            return direct
        tokens = []
        for comparison_id in value.significance_refs:
            relation = self.relations_by_id.get(comparison_id)
            if relation is None:
                continue
            if (
                relation.question_id != value.question_id
                or relation.metric_id != value.metric_id
                or value.slice_id
                not in {relation.left_slice_id, relation.right_slice_id}
            ):
                continue
            tokens.extend(
                self.tokens_by_comparison_slice.get(
                    (comparison_id, value.slice_id), ()
                )
            )
        return tuple(sorted(dict.fromkeys(tokens)))


def significance_presentation(
    comparisons: tuple[SignificanceRelation, ...],
    slices: tuple[CanonicalSlice, ...],
) -> SignificancePresentation:
    slice_labels = {
        item.slice_id: item.label or item.member_id or item.slice_id
        for item in slices
    }
    comparable_slices = sorted(
        (
            item
            for item in slices
            if not item.is_total
        ),
        key=lambda item: (
            str(item.banner_dimension_id or ""),
            str(item.member_id or ""),
            str(item.label or item.slice_id),
        ),
    )
    letters = {
        item.slice_id: _column_letter(index)
        for index, item in enumerate(comparable_slices)
    }
    token_sets: dict[str, set[str]] = {
        item.slice_id: set() for item in comparable_slices
    }
    comparison_slice_tokens: dict[tuple[str, str], tuple[str, ...]] = {}
    rows = []
    for relation in comparisons:
        status = _enum_value(relation.status)
        if status in SIGNIFICANT_STATES:
            left_letter = letters.get(relation.left_slice_id)
            right_letter = letters.get(relation.right_slice_id)
            if left_letter and right_letter:
                token_sets.setdefault(
                    relation.left_slice_id, set()
                ).add(right_letter)
                token_sets.setdefault(
                    relation.right_slice_id, set()
                ).add(left_letter)
                comparison_slice_tokens[
                    (relation.comparison_id, relation.left_slice_id)
                ] = (right_letter,)
                comparison_slice_tokens[
                    (relation.comparison_id, relation.right_slice_id)
                ] = (left_letter,)
        rows.append(
            {
                "comparison_id": relation.comparison_id,
                "question_id": relation.question_id,
                "metric_id": relation.metric_id,
                "analytical_scope": relation.analytical_scope,
                "left_slice_id": relation.left_slice_id,
                "left_label": slice_labels.get(
                    relation.left_slice_id, relation.left_slice_id
                ),
                "right_slice_id": relation.right_slice_id,
                "right_label": slice_labels.get(
                    relation.right_slice_id, relation.right_slice_id
                ),
                "status": status,
                "raw_p_value": relation.raw_p_value,
                "adjusted_p_value": relation.adjusted_p_value,
                "direction": relation.direction,
            }
        )
    legend_rows = [
        {
            "slice_id": item.slice_id,
            "Columna": slice_labels.get(item.slice_id, item.slice_id),
            "Letra": letters[item.slice_id],
        }
        for item in comparable_slices
    ]
    return SignificancePresentation(
        tokens_by_slice_id={
            slice_id: tuple(sorted(values))
            for slice_id, values in token_sets.items()
            if values
        },
        tokens_by_comparison_slice=comparison_slice_tokens,
        relations_by_id={
            relation.comparison_id: relation for relation in comparisons
        },
        legend=pd.DataFrame(legend_rows),
        table=pd.DataFrame(rows),
    )


def _column_letter(index: int) -> str:
    letters = []
    value = index
    while True:
        value, remainder = divmod(value, 26)
        letters.append(chr(ord("A") + remainder))
        if value == 0:
            break
        value -= 1
    return "".join(reversed(letters))


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))
