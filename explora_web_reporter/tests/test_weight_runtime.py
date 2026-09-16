from __future__ import annotations

from dataclasses import replace
import math
import unittest

import numpy as np
import pandas as pd

from src.analytics_core.mode import resolve_execution_mode
from src.analytics_core.universe import (
    UniverseEvaluationResult,
    UniverseEvaluationStatus,
)
from src.analytics_core.weights import (
    LEGACY_CANONICAL_INTENDED_B1_CHANGE,
    LEGACY_CANONICAL_PARITY,
    RESOLUTION_ANALYSIS_OVERRIDE,
    RESOLUTION_NONE,
    RESOLUTION_PROJECT_DEFAULT,
    WeightEvaluationContext,
    compare_legacy_canonical_weight_result,
    evaluate_weighted_base,
    resolve_active_weight,
)
from src.contracts.models import (
    ProjectSpec,
    ReleaseMetadata,
    UniverseRef,
    WeightSpec,
)
from src.contracts.vocabulary import (
    AggregateReleaseState,
    ReleaseLifecycle,
    ReleaseMode,
    StatisticalState,
)


def released() -> ReleaseMetadata:
    return ReleaseMetadata(
        state=ReleaseLifecycle.RELEASED,
        mode=ReleaseMode.MANUAL,
        decided_by="reviewer",
        decided_at="2026-09-14T00:00:00Z",
        policy_id="B1",
        policy_version="v1",
        source_hash="hash",
    )


def weight(**overrides: object) -> WeightSpec:
    values = {
        "spec_id": "weight-spec-1",
        "version": "1.0.0",
        "release": released(),
        "weight_id": "weight-total",
        "variable_ref": "POND",
        "provenance": "client-supplied",
    }
    values.update(overrides)
    return WeightSpec(**values)


def project(**overrides: object) -> ProjectSpec:
    values = {
        "spec_id": "project-spec-1",
        "version": "1.0.0",
        "release": released(),
        "project_id": "project-1",
        "dataset_fingerprint": "dataset-hash",
        "respondent_id_binding": "id_respondente",
        "project_universe_ref": "u1",
        "default_weight_ref": None,
    }
    values.update(overrides)
    return ProjectSpec(**values)


def universe_result(
    mask: dict[str, bool] | None = None,
    *,
    status: UniverseEvaluationStatus = UniverseEvaluationStatus.PASS,
    eligible_n: int | None = None,
) -> UniverseEvaluationResult:
    respondent_mask = mask or {"r1": True, "r2": True, "r3": False}
    eligible = (
        eligible_n
        if eligible_n is not None
        else sum(1 for value in respondent_mask.values() if value)
    )
    return UniverseEvaluationResult(
        universe_ref=UniverseRef("u1"),
        universe_spec_version="1.0.0",
        evaluator_rules_version="M2_UNIVERSE_V1",
        respondent_mask=respondent_mask,
        input_n=len(respondent_mask),
        eligible_n=eligible,
        excluded_n=len(respondent_mask) - eligible,
        status=status,
        traceability={"universe": "trace"},
    )


class WeightResolutionTests(unittest.TestCase):
    def test_no_weight_configured_is_unweighted_not_unit_weights(self) -> None:
        result = evaluate_weighted_base(
            universe_result(),
            WeightEvaluationContext(respondent_ids=("r1", "r2", "r3")),
        )

        self.assertEqual(result.status, AggregateReleaseState.PASS)
        self.assertEqual(result.active_weight_id, None)
        self.assertEqual(result.resolution_source, RESOLUTION_NONE)
        self.assertEqual(result.unweighted_n, 2)
        self.assertIsNone(result.weighted_n_raw)
        self.assertIsNone(result.weighted_n)
        self.assertIsNone(result.effective_n)
        self.assertEqual(result.warnings, ())
        self.assertEqual(result.source_values_by_respondent, {})

    def test_valid_project_default_resolves(self) -> None:
        spec = weight(is_project_default=True)
        context = WeightEvaluationContext(
            respondent_ids=("r1",),
            weight_specs=(spec,),
            weight_values={"POND": {"r1": 2.0}},
        )

        resolution = resolve_active_weight(context)
        result = evaluate_weighted_base(
            universe_result({"r1": True}),
            context,
        )

        self.assertEqual(resolution.source, RESOLUTION_PROJECT_DEFAULT)
        self.assertEqual(resolution.weight_spec, spec)
        self.assertEqual(result.active_weight_id, "weight-total")
        self.assertEqual(result.weighted_n_raw, 2.0)

    def test_project_spec_default_selector_resolves_and_matches_flag(self) -> None:
        spec = weight(is_project_default=True)
        context = WeightEvaluationContext(
            respondent_ids=("r1",),
            weight_specs=(spec,),
            project_spec=project(default_weight_ref="weight-total"),
            weight_values={"POND": {"r1": 1.0}},
        )

        result = evaluate_weighted_base(
            universe_result({"r1": True}),
            context,
        )

        self.assertEqual(result.status, AggregateReleaseState.PASS)
        self.assertEqual(result.resolution_source, RESOLUTION_PROJECT_DEFAULT)
        self.assertEqual(result.provenance.project_spec_id, "project-spec-1")

    def test_default_authority_conflict_is_structured_fail(self) -> None:
        context = WeightEvaluationContext(
            respondent_ids=("r1",),
            weight_specs=(weight(is_project_default=True),),
            project_spec=project(default_weight_ref="other-weight"),
            weight_values={"POND": {"r1": 1.0}},
        )

        result = evaluate_weighted_base(
            universe_result({"r1": True}),
            context,
        )

        self.assertEqual(result.status, AggregateReleaseState.FAIL)
        self.assertIn("conflicting project default", result.failures[0])

    def test_valid_analysis_override_wins_over_project_default(self) -> None:
        default = weight(
            is_project_default=True,
            variable_ref="POND_DEFAULT",
        )
        override = weight(
            spec_id="weight-spec-2",
            weight_id="weight-override",
            variable_ref="POND_OVERRIDE",
        )
        context = WeightEvaluationContext(
            respondent_ids=("r1",),
            weight_specs=(default, override),
            weight_values={
                "POND_DEFAULT": {"r1": 1.0},
                "POND_OVERRIDE": {"r1": 3.0},
            },
        )

        result = evaluate_weighted_base(
            universe_result({"r1": True}),
            context,
            analysis_weight_override="weight-override",
        )

        self.assertEqual(result.resolution_source, RESOLUTION_ANALYSIS_OVERRIDE)
        self.assertEqual(result.active_weight_id, "weight-override")
        self.assertEqual(result.weighted_n_raw, 3.0)

    def test_unknown_override_blocks_without_falling_back_to_default(self) -> None:
        context = WeightEvaluationContext(
            respondent_ids=("r1",),
            weight_specs=(weight(is_project_default=True),),
            weight_values={"POND": {"r1": 2.0}},
        )

        result = evaluate_weighted_base(
            universe_result({"r1": True}),
            context,
            analysis_weight_override="missing",
        )

        self.assertEqual(result.status, AggregateReleaseState.FAIL)
        self.assertEqual(result.resolution_source, RESOLUTION_ANALYSIS_OVERRIDE)
        self.assertIsNone(result.active_weight_id)
        self.assertIn("unknown weight override: missing", result.failures)

    def test_out_of_scope_override_blocks(self) -> None:
        context = WeightEvaluationContext(
            respondent_ids=("r1",),
            weight_specs=(
                weight(permitted_analysis_overrides=("other-weight",)),
            ),
            weight_values={"POND": {"r1": 2.0}},
        )

        result = evaluate_weighted_base(
            universe_result({"r1": True}),
            context,
            analysis_weight_override="weight-total",
        )

        self.assertEqual(result.status, AggregateReleaseState.FAIL)
        self.assertIn("out-of-scope weight override", result.failures[0])

    def test_invalid_project_default_id_blocks(self) -> None:
        context = WeightEvaluationContext(
            respondent_ids=("r1",),
            weight_specs=(weight(),),
            project_spec=project(default_weight_ref="missing-default"),
            weight_values={"POND": {"r1": 2.0}},
        )

        result = evaluate_weighted_base(
            universe_result({"r1": True}),
            context,
        )

        self.assertEqual(result.status, AggregateReleaseState.FAIL)
        self.assertIn("unknown project default weight", result.failures[0])

    def test_invalid_configured_default_blocks(self) -> None:
        invalid = weight(
            is_project_default=True,
            release=replace(released(), state=ReleaseLifecycle.APPROVED),
        )
        context = WeightEvaluationContext(
            respondent_ids=("r1",),
            weight_specs=(invalid,),
            weight_values={"POND": {"r1": 2.0}},
        )

        result = evaluate_weighted_base(
            universe_result({"r1": True}),
            context,
        )

        self.assertEqual(result.status, AggregateReleaseState.FAIL)
        self.assertIn("only RELEASED specs", result.failures[0])

    def test_name_and_ai_candidates_do_not_activate_weighting(self) -> None:
        context = WeightEvaluationContext(
            respondent_ids=("r1", "r2"),
            weight_values={"POND": {"r1": 2.0, "r2": 3.0}},
            candidate_weight_ids=("POND", "ai-recommended-weight"),
        )

        result = evaluate_weighted_base(
            universe_result({"r1": True, "r2": True}),
            context,
        )

        self.assertEqual(result.resolution_source, RESOLUTION_NONE)
        self.assertIsNone(result.active_weight_id)
        self.assertIsNone(result.weighted_n_raw)


class WeightValueAndBaseTests(unittest.TestCase):
    def context(self, values: dict[str, object]) -> WeightEvaluationContext:
        return WeightEvaluationContext(
            respondent_ids=tuple(values),
            weight_specs=(weight(is_project_default=True),),
            weight_values={"POND": values},
        )

    def test_all_positive_finite_weights_pass(self) -> None:
        result = evaluate_weighted_base(
            universe_result({"r1": True, "r2": True, "r3": True}),
            self.context({"r1": 1.0, "r2": 2.0, "r3": 3.0}),
        )

        self.assertEqual(result.status, AggregateReleaseState.PASS)
        self.assertEqual(result.unweighted_n, 3)
        self.assertEqual(result.weighted_n_raw, 6.0)
        self.assertEqual(result.weighted_n, result.weighted_n_raw)
        self.assertAlmostEqual(result.effective_n, 36.0 / 14.0)

    def test_missing_nan_and_non_numeric_are_excluded_not_imputed(self) -> None:
        result = evaluate_weighted_base(
            universe_result({"r1": True, "r2": True, "r3": True, "r4": True}),
            self.context(
                {"r1": 1.5, "r2": None, "r3": math.nan, "r4": "1.5"}
            ),
        )

        self.assertEqual(result.status, AggregateReleaseState.PASS_WITH_WARNINGS)
        self.assertEqual(result.unweighted_n, 4)
        self.assertEqual(result.weighted_n_raw, 1.5)
        self.assertEqual(result.weighted_n, 1.5)
        self.assertEqual(result.qa.missing_count, 2)
        self.assertEqual(result.qa.non_numeric_count, 1)
        self.assertEqual(result.qa.non_finite_count, 0)
        self.assertEqual(result.qa.valid_weight_count, 1)
        self.assertEqual(result.source_values_by_respondent["r4"], "1.5")
        self.assertNotEqual(result.weighted_n_raw, 1.5 + 1.0 + 1.0 + 1.0)

    def test_nan_numeric_representations_are_missing_not_non_finite(self) -> None:
        nan_values = [
            float("nan"),
            np.float16(np.nan),
            np.float32(np.nan),
            np.float64(np.nan),
        ]
        if hasattr(np, "longdouble"):
            nan_values.append(np.longdouble(np.nan))

        for value in nan_values:
            with self.subTest(type=type(value).__name__):
                result = evaluate_weighted_base(
                    universe_result({"r1": True, "r2": True}),
                    self.context({"r1": 1.0, "r2": value}),
                )

                self.assertEqual(
                    result.status, AggregateReleaseState.PASS_WITH_WARNINGS
                )
                self.assertEqual(result.unweighted_n, 2)
                self.assertEqual(result.weighted_n_raw, 1.0)
                self.assertEqual(result.weighted_n, 1.0)
                self.assertEqual(result.qa.missing_count, 1)
                self.assertEqual(result.qa.non_finite_count, 0)
                self.assertEqual(result.qa.valid_weight_count, 1)
                self.assertAlmostEqual(result.effective_n, 1.0)

    def test_pandas_series_numpy_nan_is_missing_not_non_finite(self) -> None:
        values = pd.Series([1.0, np.nan], index=["r1", "r2"]).to_dict()

        result = evaluate_weighted_base(
            universe_result({"r1": True, "r2": True}),
            self.context(values),
        )

        self.assertEqual(result.status, AggregateReleaseState.PASS_WITH_WARNINGS)
        self.assertEqual(result.unweighted_n, 2)
        self.assertEqual(result.weighted_n_raw, 1.0)
        self.assertEqual(result.weighted_n, 1.0)
        self.assertEqual(result.qa.missing_count, 1)
        self.assertEqual(result.qa.non_finite_count, 0)

    def test_numpy_float32_nan_vs_infinity_are_distinct(self) -> None:
        cases = (
            (
                np.float32(np.nan),
                AggregateReleaseState.PASS_WITH_WARNINGS,
                1,
                0,
                1.0,
            ),
            (np.float32(np.inf), AggregateReleaseState.FAIL, 0, 1, None),
            (np.float32(-np.inf), AggregateReleaseState.FAIL, 0, 1, None),
        )

        for value, status, missing_count, non_finite_count, weighted_n in cases:
            with self.subTest(value=str(value)):
                result = evaluate_weighted_base(
                    universe_result({"r1": True, "r2": True}),
                    self.context({"r1": 1.0, "r2": value}),
                )

                self.assertEqual(result.status, status)
                self.assertEqual(result.unweighted_n, 2)
                self.assertEqual(result.qa.missing_count, missing_count)
                self.assertEqual(result.qa.non_finite_count, non_finite_count)
                self.assertEqual(result.weighted_n_raw, weighted_n)
                self.assertEqual(result.weighted_n, weighted_n)

    def test_nan_does_not_change_m2_mask_or_become_one(self) -> None:
        m2 = universe_result({"r1": True, "r2": True})
        original_mask = dict(m2.respondent_mask)

        result = evaluate_weighted_base(
            m2,
            self.context({"r1": 1.0, "r2": np.float32(np.nan)}),
        )

        self.assertEqual(m2.respondent_mask, original_mask)
        self.assertEqual(result.unweighted_n, 2)
        self.assertEqual(result.weighted_n_raw, 1.0)
        self.assertEqual(result.weighted_n, 1.0)
        self.assertEqual(result.qa.missing_count, 1)
        self.assertNotEqual(result.weighted_n_raw, 2.0)

    def test_positive_and_negative_infinity_block(self) -> None:
        for value in (math.inf, -math.inf):
            with self.subTest(value=value):
                result = evaluate_weighted_base(
                    universe_result({"r1": True}),
                    self.context({"r1": value}),
                )

                self.assertEqual(result.status, AggregateReleaseState.FAIL)
                self.assertIsNone(result.weighted_n_raw)
                self.assertEqual(result.qa.non_finite_count, 1)

    def test_negative_weight_is_unsupported_v1_and_blocks(self) -> None:
        result = evaluate_weighted_base(
            universe_result({"r1": True, "r2": True}),
            self.context({"r1": 1.0, "r2": -0.5}),
        )

        self.assertEqual(result.status, AggregateReleaseState.FAIL)
        self.assertEqual(result.qa.negative_count, 1)
        self.assertIn("UNSUPPORTED V1", result.failures[0])
        self.assertIsNone(result.weighted_n)

    def test_zero_weight_mixed_with_positive_is_valid(self) -> None:
        result = evaluate_weighted_base(
            universe_result({"r1": True, "r2": True, "r3": True}),
            self.context({"r1": 0.0, "r2": 1.5, "r3": 2.5}),
        )

        self.assertEqual(result.status, AggregateReleaseState.PASS)
        self.assertEqual(result.unweighted_n, 3)
        self.assertEqual(result.qa.zero_count, 1)
        self.assertEqual(result.qa.valid_weight_count, 3)
        self.assertEqual(result.weighted_n_raw, 4.0)
        self.assertEqual(result.weighted_n, 4.0)

    def test_all_zero_has_no_calculable_weighted_base(self) -> None:
        result = evaluate_weighted_base(
            universe_result({"r1": True, "r2": True}),
            self.context({"r1": 0.0, "r2": 0.0}),
        )

        self.assertEqual(result.status, AggregateReleaseState.FAIL)
        self.assertEqual(result.unweighted_n, 2)
        self.assertIsNone(result.weighted_n_raw)
        self.assertIsNone(result.weighted_n)
        self.assertIsNone(result.effective_n)
        self.assertIn("no positive total applied weight", result.failures)

    def test_zero_eligible_universe_is_not_reclassified_as_universe_fail(
        self,
    ) -> None:
        m2 = universe_result({"r1": False, "r2": False}, eligible_n=0)

        result = evaluate_weighted_base(
            m2,
            self.context({"r1": 1.0, "r2": 2.0}),
        )

        self.assertEqual(m2.status, UniverseEvaluationStatus.PASS)
        self.assertEqual(m2.eligible_n, 0)
        self.assertEqual(result.status, AggregateReleaseState.PASS_WITH_WARNINGS)
        self.assertEqual(result.unweighted_n, 0)
        self.assertEqual(result.weighted_n_raw, 0.0)
        self.assertIn("effective_n unavailable", result.warnings[0])

    def test_canonical_base_golden_values_and_no_rounding(self) -> None:
        values = {
            "r1": 0.0,
            "r2": 0.5,
            "r3": 1.0,
            "r4": 1.5,
            "r5": 2.0,
        }
        result = evaluate_weighted_base(
            universe_result({respondent_id: True for respondent_id in values}),
            self.context(values),
        )

        self.assertEqual(result.unweighted_n, 5)
        self.assertEqual(result.weighted_n_raw, 5.0)
        self.assertEqual(result.weighted_n, result.weighted_n_raw)
        self.assertAlmostEqual(result.effective_n, 25.0 / 7.5)
        self.assertEqual(result.qa.distribution.minimum, 0.0)
        self.assertEqual(result.qa.distribution.maximum, 2.0)

    def test_kish_scale_invariance_and_weighted_n_scale_change(self) -> None:
        base = {"r1": 0.5, "r2": 1.0, "r3": 2.0}
        scaled = {key: value * 7.0 for key, value in base.items()}
        mask = {key: True for key in base}

        left = evaluate_weighted_base(
            universe_result(mask),
            self.context(base),
        )
        right = evaluate_weighted_base(
            universe_result(mask),
            self.context(scaled),
        )

        self.assertAlmostEqual(
            right.weighted_n_raw,
            left.weighted_n_raw * 7.0,
        )
        self.assertAlmostEqual(right.weighted_n, left.weighted_n * 7.0)
        self.assertAlmostEqual(right.effective_n, left.effective_n)

    def test_weighted_n_equality_for_valid_v1_weight_styles(self) -> None:
        cases = (
            {"r1": 1.0, "r2": 2.0},
            {"r1": 0.0, "r2": 2.0},
            {"r1": 0.25, "r2": 1.75},
            {"r1": 100.0, "r2": 250.0},
            {"r1": 0.8, "r2": 1.2},
            {"r1": 0.75, "r2": 1.25, "r3": 3.0},
        )
        for values in cases:
            with self.subTest(values=values):
                result = evaluate_weighted_base(
                    universe_result({key: True for key in values}),
                    self.context(values),
                    external_normalization_provenance="upstream normalized",
                    external_trimming_provenance="upstream trimmed",
                )

                self.assertEqual(result.status, AggregateReleaseState.PASS)
                self.assertEqual(result.weighted_n_raw, result.weighted_n)

    def test_extreme_positive_weights_are_diagnostics_not_failures(self) -> None:
        result = evaluate_weighted_base(
            universe_result({"r1": True, "r2": True, "r3": True}),
            self.context({"r1": 1.0, "r2": 1.0, "r3": 1_000_000.0}),
        )

        self.assertEqual(result.status, AggregateReleaseState.PASS)
        self.assertEqual(result.failures, ())
        self.assertEqual(result.qa.distribution.maximum, 1_000_000.0)
        self.assertEqual(result.qa.distribution.max_min_positive_ratio, 1_000_000.0)


class WeightM2AndSignificanceTests(unittest.TestCase):
    def test_m2_mask_is_consumed_not_modified_by_weighting(self) -> None:
        m2 = universe_result({"r1": True, "r2": False, "r3": True})
        context = WeightEvaluationContext(
            respondent_ids=("r1", "r2", "r3"),
            weight_specs=(weight(is_project_default=True),),
            weight_values={"POND": {"r1": 0.0, "r2": 999.0, "r3": None}},
        )

        weighted = evaluate_weighted_base(m2, context)
        unweighted = evaluate_weighted_base(
            m2,
            WeightEvaluationContext(respondent_ids=("r1", "r2", "r3")),
        )

        self.assertEqual(m2.respondent_mask, {"r1": True, "r2": False, "r3": True})
        self.assertEqual(m2.eligible_n, 2)
        self.assertEqual(weighted.m2_universe_result.respondent_mask, m2.respondent_mask)
        self.assertEqual(unweighted.m2_universe_result.respondent_mask, m2.respondent_mask)
        self.assertEqual(weighted.unweighted_n, 2)
        self.assertEqual(unweighted.unweighted_n, 2)

    def test_metric_validity_is_applied_before_weight_contribution(self) -> None:
        context = WeightEvaluationContext(
            respondent_ids=("r1", "r2", "r3"),
            weight_specs=(weight(is_project_default=True),),
            weight_values={"POND": {"r1": 1.0, "r2": 2.0, "r3": 4.0}},
        )

        result = evaluate_weighted_base(
            universe_result({"r1": True, "r2": True, "r3": True}),
            context,
            metric_valid_mask={"r1": True, "r2": False, "r3": True},
        )

        self.assertEqual(result.unweighted_n, 2)
        self.assertEqual(result.weighted_n_raw, 5.0)
        self.assertNotIn("r2", result.source_values_by_respondent)

    def test_m2_fail_and_unsupported_are_propagated_without_repair(self) -> None:
        context = WeightEvaluationContext(
            respondent_ids=("r1",),
            weight_specs=(weight(is_project_default=True),),
            weight_values={"POND": {"r1": 1.0}},
        )
        cases = (
            (UniverseEvaluationStatus.FAIL, AggregateReleaseState.FAIL),
            (
                UniverseEvaluationStatus.UNSUPPORTED,
                AggregateReleaseState.REVIEW_REQUIRED,
            ),
        )
        for m2_status, expected in cases:
            with self.subTest(m2_status=m2_status):
                result = evaluate_weighted_base(
                    universe_result({"r1": False}, status=m2_status, eligible_n=0),
                    context,
                )

                self.assertEqual(result.status, expected)
                self.assertIn("M2 Universe dependency", result.failures[0])
                self.assertIsNone(result.weighted_n_raw)

    def test_significance_not_requested_leaves_guard_not_tested(self) -> None:
        result = evaluate_weighted_base(
            universe_result({"r1": True}),
            WeightEvaluationContext(
                respondent_ids=("r1",),
                weight_specs=(weight(is_project_default=True),),
                weight_values={"POND": {"r1": 1.0}},
            ),
        )

        self.assertEqual(result.significance_status, StatisticalState.NOT_TESTED)
        self.assertIsNone(result.significance_reason)

    def test_weighted_significance_requested_is_unsupported_not_descriptive_fail(
        self,
    ) -> None:
        result = evaluate_weighted_base(
            universe_result({"r1": True, "r2": True}),
            WeightEvaluationContext(
                respondent_ids=("r1", "r2"),
                weight_specs=(weight(is_project_default=True),),
                weight_values={"POND": {"r1": 1.0, "r2": 2.0}},
            ),
            significance_requested=True,
        )

        self.assertEqual(result.status, AggregateReleaseState.PASS_WITH_WARNINGS)
        self.assertEqual(result.weighted_n_raw, 3.0)
        self.assertEqual(result.significance_status, StatisticalState.UNSUPPORTED)
        self.assertIn("weighted significance is UNSUPPORTED V1", result.warnings)
        self.assertNotIn("p_value", result.__dataclass_fields__)
        self.assertNotIn("letters", result.__dataclass_fields__)

    def test_weight_runtime_does_not_import_unweighted_significance_engine(self) -> None:
        import ast
        from pathlib import Path

        path = Path(__file__).resolve().parents[1] / "src" / "analytics_core" / "weights.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }

        self.assertNotIn("src.reporter.significance", imports)


class WeightQAProvenanceAndRegressionTests(unittest.TestCase):
    def test_qa_counts_rates_distribution_and_provenance_are_recorded(self) -> None:
        spec = weight(is_project_default=True, provenance="client supplied / rim")
        context = WeightEvaluationContext(
            respondent_ids=("r1", "r2", "r3", "r4"),
            weight_specs=(spec,),
            weight_values={"POND": {"r1": 0.0, "r2": 2.0, "r3": None, "r4": "bad"}},
            project_spec=project(default_weight_ref="weight-total"),
            analysis_config_version="analysis-v1",
            analytical_scope="question",
            traceability={"run": "trace"},
        )

        result = evaluate_weighted_base(
            universe_result({"r1": True, "r2": True, "r3": True, "r4": True}),
            context,
        )

        self.assertEqual(result.qa.active_weight_id, "weight-total")
        self.assertEqual(result.qa.source_variable, "POND")
        self.assertEqual(result.qa.resolution_source, RESOLUTION_PROJECT_DEFAULT)
        self.assertEqual(result.qa.unweighted_n, 4)
        self.assertEqual(result.qa.valid_weight_count, 2)
        self.assertEqual(result.qa.zero_count, 1)
        self.assertEqual(result.qa.missing_count, 1)
        self.assertEqual(result.qa.non_numeric_count, 1)
        self.assertEqual(result.qa.missing_rate, 0.25)
        self.assertEqual(result.qa.non_numeric_rate, 0.25)
        self.assertEqual(result.qa.weighted_n_raw, 2.0)
        self.assertEqual(result.qa.weighted_n, 2.0)
        self.assertEqual(result.provenance.project_id, "project-1")
        self.assertEqual(result.provenance.dataset_fingerprint, "dataset-hash")
        self.assertEqual(result.provenance.analysis_config_version, "analysis-v1")
        self.assertEqual(result.provenance.weight_spec_version, "1.0.0")
        self.assertEqual(result.provenance.b1_policy_id, "B1")
        self.assertEqual(result.traceability["run"], "trace")

    def test_external_normalization_and_trimming_are_provenance_only(self) -> None:
        result = evaluate_weighted_base(
            universe_result({"r1": True, "r2": True}),
            WeightEvaluationContext(
                respondent_ids=("r1", "r2"),
                weight_specs=(weight(is_project_default=True),),
                weight_values={"POND": {"r1": 0.8, "r2": 1.2}},
            ),
            external_normalization_provenance="supplier normalized to project N",
            external_trimming_provenance="supplier trimmed p99",
        )

        self.assertEqual(result.status, AggregateReleaseState.PASS)
        self.assertEqual(result.weighted_n_raw, 2.0)
        self.assertEqual(result.weighted_n, 2.0)
        self.assertEqual(
            result.provenance.external_normalization_provenance,
            "supplier normalized to project N",
        )
        self.assertEqual(
            result.provenance.external_trimming_provenance,
            "supplier trimmed p99",
        )

    def test_legacy_canonical_differences_must_be_classified(self) -> None:
        canonical = evaluate_weighted_base(
            universe_result({"r1": True, "r2": True}),
            WeightEvaluationContext(
                respondent_ids=("r1", "r2"),
                weight_specs=(weight(is_project_default=True),),
                weight_values={"POND": {"r1": 2.0, "r2": None}},
            ),
        )

        parity = compare_legacy_canonical_weight_result(
            canonical,
            {
                "unweighted_n": canonical.unweighted_n,
                "weighted_n_raw": canonical.weighted_n_raw,
                "weighted_n": canonical.weighted_n,
                "effective_n": canonical.effective_n,
                "status": canonical.status,
            },
            classification=LEGACY_CANONICAL_PARITY,
        )
        intended = compare_legacy_canonical_weight_result(
            canonical,
            {"weighted_n_raw": 3.0},
            classification=LEGACY_CANONICAL_INTENDED_B1_CHANGE,
            reason="legacy missing weight replacement with 1.0",
        )

        self.assertEqual(parity.classification, LEGACY_CANONICAL_PARITY)
        self.assertEqual(parity.deltas, {})
        self.assertEqual(
            intended.classification,
            LEGACY_CANONICAL_INTENDED_B1_CHANGE,
        )
        self.assertIn("weighted_n_raw", intended.deltas)

    def test_default_execution_mode_still_legacy_and_rollback_needs_no_migration(
        self,
    ) -> None:
        result = evaluate_weighted_base(
            universe_result({"r1": True}),
            WeightEvaluationContext(respondent_ids=("r1",)),
        )

        self.assertEqual(resolve_execution_mode(environ={}).value, "LEGACY")
        self.assertEqual(result.resolution_source, RESOLUTION_NONE)
        self.assertIsNone(result.active_weight_id)
        self.assertIsNone(result.weighted_n)


if __name__ == "__main__":
    unittest.main()
