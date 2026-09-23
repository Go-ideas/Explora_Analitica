from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import mean, stdev
from typing import Callable

from src.contracts.models import FormulaRegistryEntry
from src.contracts.vocabulary import ValueStatus, ValueUnit


FORMULA_REGISTRY_VERSION = "M5_FORMULA_REGISTRY_V1"


class FormulaRegistryError(ValueError):
    pass


@dataclass(frozen=True)
class FormulaResult:
    value_status: ValueStatus
    unit: ValueUnit
    estimate: float | int | None
    numerator: float | int | None = None
    denominator: float | int | None = None
    reason: str = ""


@dataclass(frozen=True)
class FormulaDefinition:
    entry: FormulaRegistryEntry
    evaluator: Callable[..., FormulaResult]

    def supports(self, *, structure_type: str, weight_mode: str) -> bool:
        return (
            structure_type in self.entry.supported_structures
            and weight_mode in self.entry.supported_weight_modes
        )


SUPPORTED_STRUCTURES = (
    "RU",
    "RM",
    "GRID_ESCALA",
    "GRID_RM",
    "LOOP_RM",
    "LOOP_RU",
    "LOOP_NUMERICO",
)
SUPPORTED_WEIGHT_MODES = ("unweighted", "weighted")


def get_formula(formula_id: str) -> FormulaDefinition:
    try:
        return FORMULA_REGISTRY[formula_id]
    except KeyError as exc:
        raise FormulaRegistryError(f"unknown formula_id: {formula_id}") from exc


def evaluate_formula(
    formula_id: str,
    *,
    structure_type: str,
    weight_mode: str = "unweighted",
    denominator: float | int | None = None,
    numerator: float | int | None = None,
    observations: tuple[float, ...] = (),
    observation_weights: tuple[float, ...] = (),
    promoters: int | None = None,
    detractors: int | None = None,
) -> FormulaResult:
    formula = get_formula(formula_id)
    if not formula.supports(
        structure_type=structure_type,
        weight_mode=weight_mode,
    ):
        return FormulaResult(
            ValueStatus.UNSUPPORTED,
            _unit_for(formula_id),
            None,
            numerator=numerator,
            denominator=denominator,
            reason="known formula unsupported for structure/weight combination",
        )
    return formula.evaluator(
        denominator=denominator,
        numerator=numerator,
        observations=observations,
        observation_weights=observation_weights,
        promoters=promoters,
        detractors=detractors,
    )


def _count(**kwargs: object) -> FormulaResult:
    numerator = kwargs.get("numerator")
    value = numerator if numerator is not None else kwargs.get("denominator")
    if value is None:
        return FormulaResult(ValueStatus.NO_VALID_BASE, ValueUnit.COUNT, None)
    if not _is_finite_number(value):
        return FormulaResult(
            ValueStatus.ERROR,
            ValueUnit.COUNT,
            None,
            numerator=None,
            reason="non-finite count input",
        )
    return FormulaResult(ValueStatus.OK, ValueUnit.COUNT, value, numerator=value)


def _proportion(**kwargs: object) -> FormulaResult:
    numerator = kwargs.get("numerator")
    denominator = kwargs.get("denominator")
    if not _is_finite_number(numerator) or not _is_finite_number(denominator):
        return FormulaResult(
            ValueStatus.ERROR,
            ValueUnit.PROPORTION,
            None,
            numerator=None,
            denominator=None,
            reason="non-finite proportion input",
        )
    if denominator is None or denominator <= 0:
        return FormulaResult(
            ValueStatus.NO_VALID_BASE,
            ValueUnit.PROPORTION,
            None,
            numerator=numerator,
            denominator=denominator,
        )
    if numerator is None:
        return FormulaResult(
            ValueStatus.ERROR,
            ValueUnit.PROPORTION,
            None,
            denominator=denominator,
            reason="proportion numerator is required",
        )
    try:
        estimate = numerator / denominator
    except OverflowError:
        estimate = math.inf
    if not math.isfinite(estimate):
        return FormulaResult(
            ValueStatus.ERROR,
            ValueUnit.PROPORTION,
            None,
            numerator=numerator,
            denominator=denominator,
            reason="non-finite proportion result",
        )
    return FormulaResult(
        ValueStatus.OK,
        ValueUnit.PROPORTION,
        estimate,
        numerator=numerator,
        denominator=denominator,
    )


def _mean(**kwargs: object) -> FormulaResult:
    observations, invalid_count = _checked_observations(
        kwargs.get("observations", ())
    )
    if invalid_count:
        return FormulaResult(
            ValueStatus.ERROR,
            ValueUnit.MEAN,
            None,
            denominator=len(observations),
            reason="non-finite mean input",
        )
    if not observations:
        return FormulaResult(ValueStatus.NO_VALID_BASE, ValueUnit.MEAN, None)
    weights, invalid_weights = _checked_observations(
        kwargs.get("observation_weights", ())
    )
    if weights:
        if invalid_weights or len(weights) != len(observations) or any(weight < 0 for weight in weights) or sum(weights) <= 0:
            return FormulaResult(
                ValueStatus.ERROR,
                ValueUnit.MEAN,
                None,
                denominator=len(observations),
                reason="invalid weighted mean input",
            )
        estimate = sum(value * weight for value, weight in zip(observations, weights)) / sum(weights)
    else:
        estimate = mean(observations)
    if not math.isfinite(estimate):
        return FormulaResult(
            ValueStatus.ERROR,
            ValueUnit.MEAN,
            None,
            denominator=len(observations),
            reason="non-finite mean result",
        )
    return FormulaResult(
        ValueStatus.OK,
        ValueUnit.MEAN,
        estimate,
        denominator=len(observations),
    )


def _standard_deviation(**kwargs: object) -> FormulaResult:
    observations, invalid_count = _checked_observations(
        kwargs.get("observations", ())
    )
    if invalid_count:
        return FormulaResult(
            ValueStatus.ERROR,
            ValueUnit.STANDARD_DEVIATION,
            None,
            denominator=len(observations),
            reason="non-finite standard deviation input",
        )
    if len(observations) < 2:
        return FormulaResult(
            ValueStatus.NO_VALID_BASE,
            ValueUnit.STANDARD_DEVIATION,
            None,
            denominator=len(observations),
        )
    estimate = stdev(observations)
    if not math.isfinite(estimate):
        return FormulaResult(
            ValueStatus.ERROR,
            ValueUnit.STANDARD_DEVIATION,
            None,
            denominator=len(observations),
            reason="non-finite standard deviation result",
        )
    return FormulaResult(
        ValueStatus.OK,
        ValueUnit.STANDARD_DEVIATION,
        estimate,
        denominator=len(observations),
    )


def _nps(**kwargs: object) -> FormulaResult:
    promoters = kwargs.get("promoters")
    detractors = kwargs.get("detractors")
    denominator = kwargs.get("denominator")
    if (
        not _is_finite_number(promoters)
        or not _is_finite_number(detractors)
        or not _is_finite_number(denominator)
    ):
        return FormulaResult(
            ValueStatus.ERROR,
            ValueUnit.SCORE,
            None,
            denominator=None,
            reason="non-finite NPS input",
        )
    if denominator is None or denominator <= 0:
        return FormulaResult(
            ValueStatus.NO_VALID_BASE,
            ValueUnit.SCORE,
            None,
            denominator=denominator,
        )
    if promoters is None or detractors is None:
        return FormulaResult(
            ValueStatus.ERROR,
            ValueUnit.SCORE,
            None,
            denominator=denominator,
            reason="NPS requires promoter and detractor counts",
        )
    try:
        estimate = (promoters - detractors) / denominator
    except OverflowError:
        estimate = math.inf
    if not math.isfinite(estimate):
        return FormulaResult(
            ValueStatus.ERROR,
            ValueUnit.SCORE,
            None,
            numerator=promoters - detractors,
            denominator=denominator,
            reason="non-finite NPS result",
        )
    return FormulaResult(
        ValueStatus.OK,
        ValueUnit.SCORE,
        estimate,
        numerator=promoters - detractors,
        denominator=denominator,
    )


def _checked_observations(values: object) -> tuple[tuple[float, ...], int]:
    result = []
    invalid_count = 0
    for value in values or ():
        candidate = float(value)
        if not math.isfinite(candidate):
            invalid_count += 1
            continue
        result.append(candidate)
    return tuple(result), invalid_count


def _is_finite_number(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value))


def _unit_for(formula_id: str) -> ValueUnit:
    if formula_id == "COUNT":
        return ValueUnit.COUNT
    if formula_id in {
        "FREQUENCY",
        "PROPORTION",
        "TOP_BOX",
        "BOTTOM_BOX",
        "RM_RESPONDENT_PROPORTION",
        "RM_MENTION_PROPORTION",
    }:
        return ValueUnit.PROPORTION
    if formula_id == "STANDARD_DEVIATION":
        return ValueUnit.STANDARD_DEVIATION
    if formula_id == "NPS_DESCRIPTIVE":
        return ValueUnit.SCORE
    return ValueUnit.MEAN


def _entry(
    formula_id: str,
    denominator_requirements: tuple[str, ...],
    structures: tuple[str, ...] = SUPPORTED_STRUCTURES,
    weights: tuple[str, ...] = SUPPORTED_WEIGHT_MODES,
    *,
    significance_compatible: bool = False,
) -> FormulaRegistryEntry:
    return FormulaRegistryEntry(
        formula_id=formula_id,
        formula_version=FORMULA_REGISTRY_VERSION,
        input_requirements=("released_metric_spec", "canonical_base"),
        denominator_requirements=denominator_requirements,
        supported_structures=structures,
        supported_weight_modes=weights,
        significance_compatible=significance_compatible,
    )


FORMULA_REGISTRY = {
    "COUNT": FormulaDefinition(_entry("COUNT", ("any",)), _count),
    "FREQUENCY": FormulaDefinition(
        _entry("FREQUENCY", ("positive_base",), significance_compatible=True),
        _proportion,
    ),
    "PROPORTION": FormulaDefinition(
        _entry("PROPORTION", ("positive_base",), significance_compatible=True),
        _proportion,
    ),
    "MEAN": FormulaDefinition(
        _entry("MEAN", ("valid_observations",), significance_compatible=True),
        _mean,
    ),
    "STANDARD_DEVIATION": FormulaDefinition(
        _entry("STANDARD_DEVIATION", ("valid_observations_2plus",)),
        _standard_deviation,
    ),
    "TOP_BOX": FormulaDefinition(_entry("TOP_BOX", ("positive_base",)), _proportion),
    "BOTTOM_BOX": FormulaDefinition(
        _entry("BOTTOM_BOX", ("positive_base",)),
        _proportion,
    ),
    "NPS_DESCRIPTIVE": FormulaDefinition(
        _entry(
            "NPS_DESCRIPTIVE",
            ("positive_base",),
            structures=("RU",),
            weights=("unweighted",),
        ),
        _nps,
    ),
    "RM_RESPONDENT_PROPORTION": FormulaDefinition(
        _entry(
            "RM_RESPONDENT_PROPORTION",
            ("respondent_denominator",),
            structures=("RM", "GRID_RM", "LOOP_RM"),
        ),
        _proportion,
    ),
    "RM_MENTION_PROPORTION": FormulaDefinition(
        _entry(
            "RM_MENTION_PROPORTION",
            ("mention_denominator",),
            structures=("RM", "GRID_RM", "LOOP_RM"),
            weights=("unweighted",),
        ),
        _proportion,
    ),
    "SCALE_MEAN": FormulaDefinition(
        _entry("SCALE_MEAN", ("valid_observations",), structures=("RU", "GRID_ESCALA", "LOOP_RU", "LOOP_NUMERICO")),
        _mean,
    ),
}
