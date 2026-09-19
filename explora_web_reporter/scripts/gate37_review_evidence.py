"""Generate portable generic renderer review evidence; workbook outputs stay external."""
import argparse
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    repository = root.parent
    require_external = args.evidence.parent.resolve().is_relative_to(repository.resolve())
    if require_external:
        raise ValueError("Runtime evidence and workbook derivatives must remain external")
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "tests"))
    from m7b_fixtures import FIXTURE_SHA, VBA_SHA, build_test_master, request_for
    from src.analytics_core.result_identity import canonical_payload
    from src.excel_renderer import plan_render, render
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="generic_m7b_review_", dir=args.evidence.parent) as temp:
        source = Path(temp) / "master.xlsm"
        master = build_test_master(source)
        request = request_for(master)
        plan = plan_render(request, source)
        output = Path(temp) / "rendered.xlsm"
        qa = render(request, source, output, plan=plan)
        result = {
            "gate": 37, "starting_main": "d74ba842bc05be1ef327047cbfa72ebbbc2e6f8c",
            "branch": "feature/m7b-renderer-implementation", "authorized_fixture_sha256": FIXTURE_SHA,
            "vba_before_sha256": VBA_SHA, "vba_after_sha256": qa["vba_after"],
            "generic_declared_write_count": len(plan.writes), "plan_sha256": plan.plan_sha256,
            "render_plan": canonical_payload(plan), "qa": qa,
            "customer_workbook_source": False, "customer_vba_source": False,
            "excel_com_runtime_dependency": False,
            "runtime_workbooks_retained": False,
        }
        args.evidence.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
        print(json.dumps({"qa": qa["qa"], "plan": plan.plan_sha256, "writes": len(plan.writes),
                          "vba_before": VBA_SHA, "vba_after": qa["vba_after"]}, indent=2))


if __name__ == "__main__":
    main()
