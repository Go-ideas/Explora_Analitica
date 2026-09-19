"""Generate deterministic, non-customer B2 Core qualification evidence."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analytics_core.result_identity import stable_json
from src.analytics_core.significance import ENGINE_VERSION, ProportionComparisonInput, execute_proportion_family
from src.contracts.models import ReleaseMetadata, SignificanceSpec
from src.contracts.vocabulary import ReleaseLifecycle, ReleaseMode


def spec(confidence):
    release = ReleaseMetadata(ReleaseLifecycle.RELEASED, ReleaseMode.REVIEW, "B2_REVIEW",
        "2026-09-19", "B2", "B2_V1", "SIGNIFICANCE_POLICY_CANONICAL")
    return SignificanceSpec("B2_QUALIFICATION", "1.0.0", release, "pooled_z",
                            confidence=confidence, alpha=1-confidence)


def case(case_id, left, right, left_n=100, right_n=100, confidence=0.95):
    item = ProportionComparisonInput("A", "B", "slice_a", "slice_b", left, right, left_n, right_n)
    relation = execute_proportion_family(spec=spec(confidence), result_run_id="gate39a-run",
        question_id="Q_QUALIFICATION", metric_id="PROPORTION", analytical_scope="banner",
        family_id=f"family_{case_id}", comparisons=(item,))[0]
    return {"case_id": case_id, "input": asdict(item), "output": asdict(relation)}


def main():
    destination = Path(sys.argv[1])
    if destination.exists():
        raise SystemExit("Evidence destination exists")
    cases = [case("significant_90", 70, 30, confidence=.90),
             case("significant_95", 70, 30, confidence=.95),
             case("significant_99", 70, 30, confidence=.99),
             case("non_significant", 52, 48), case("ineligible_n", 20, 15, 29, 30),
             case("ineligible_expected_count", 1, 0)]
    payload = {"schema_version": "GATE39A_B2_CORE_EVIDENCE_V1",
        "policy_authority": "SIGNIFICANCE_POLICY_CANONICAL.md / B2_V1",
        "engine_version": ENGINE_VERSION, "fixture_id": "B2_SYNTHETIC_PROPORTION_QUALIFICATION_V1",
        "fixture_classification": "deterministic synthetic non-customer qualification data",
        "cases": cases, "deterministic": cases == [case(**{
            "case_id": c["case_id"], "left": c["input"]["left_numerator"],
            "right": c["input"]["right_numerator"], "left_n": c["input"]["left_unweighted_n"],
            "right_n": c["input"]["right_unweighted_n"],
            "confidence": c["output"]["confidence"]}) for c in cases],
        "reporter_dependency": "NONE", "excel_m7_changes": "NONE"}
    payload["fixture_sha256"] = hashlib.sha256(stable_json(
        [{"case_id": c["case_id"], "input": c["input"]} for c in cases]).encode()).hexdigest()
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(stable_json({"deterministic": payload["deterministic"], "fixture_sha256": payload["fixture_sha256"]}))


if __name__ == "__main__":
    main()
