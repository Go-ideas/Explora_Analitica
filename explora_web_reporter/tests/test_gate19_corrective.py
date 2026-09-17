from dataclasses import replace
from types import SimpleNamespace

import pandas as pd
import pytest

from m6_fixtures import canonical_result
from src.contracts.vocabulary import DenominatorUnit, ValueUnit
from src.web_canonical.identity_bridge import LegacyIdentityBridge
from src.web_canonical.legacy_projection import legacy_comparison_records_from_report
from src.web_canonical.request_binding import CanonicalRequestBindingError, WebCanonicalRequest, request_observability, validate_request_binding


def projection(label="Visible label", structure="RU", mention=False):
    result = canonical_result(unit=ValueUnit.PROPORTION)
    total = replace(result.slices[0], is_total=True, banner_dimension_id=None, member_id=None)
    base = replace(result.bases[0], structure_id="released-structure", slice_id=total.slice_id, denominator_unit=DenominatorUnit.MENTION if mention else DenominatorUnit.RESPONDENT)
    if mention:
        base = replace(base, provenance_refs=("m4_resolved_scope_type:PARENT_RM", "m4_resolved_scope_ref:released-structure"))
    value = replace(result.values[0], question_id="Q1", structure_id="released-structure", option_id="stable", category_id="stable" if structure == "RU" else None, slice_id=total.slice_id, base_id=base.base_id)
    result = replace(result, slices=(total,), bases=(base,), values=(value,))
    legacy = SimpleNamespace(question_id="Q1", summary=pd.DataFrame([{"banner": "Total", "respuesta": label, "porcentaje": .5, "pct_respondentes": .5, "pct_menciones": .5, "base": base.unweighted_n, "base_menciones": base.unweighted_n}]), identity_rows=pd.DataFrame([{"banner": "Total", "respuesta": label, "source_variable": "physical", "codigo_respuesta": 7, "banner_variable": "", "banner_raw_value": ""}]))
    bridge = LegacyIdentityBridge("Q1", "released-structure", structure, (("stable", "physical", "7" if structure == "RU" else None),), provenance_refs=("runtime:verified",))
    return legacy, result, bridge


@pytest.mark.parametrize("structure,mention", [("RU", False), ("RM", False), ("RM", True)])
@pytest.mark.parametrize("label", ["First label", "Entirely changed label"])
def test_stable_projection_survives_labels(structure, mention, label):
    legacy, result, bridge = projection(label, structure, mention)
    records, limitations = legacy_comparison_records_from_report(legacy, result, identity_bridge=bridge)
    assert len(records) == 1
    assert not limitations
    assert next(iter(records.values())).value == .5


@pytest.mark.parametrize("kind", ["missing", "duplicate", "conflict", "unsupported", "missing_provenance", "wrong_question", "wrong_structure", "ambiguous", "missing_metadata", "label_only"])
def test_identity_ambiguity_fails_closed(kind):
    legacy, result, bridge = projection()
    if kind == "missing":
        bridge = replace(bridge, rows=())
    elif kind == "duplicate":
        bridge = replace(bridge, rows=bridge.rows * 2)
    elif kind == "conflict":
        bridge = replace(bridge, rows=bridge.rows + (("other", "physical", "7"),))
    elif kind == "unsupported":
        bridge = replace(bridge, structure_type="GRID_RM")
    elif kind == "missing_provenance":
        bridge = replace(bridge, provenance_refs=())
    elif kind == "wrong_question":
        bridge = replace(bridge, question_id="other")
    elif kind == "wrong_structure":
        bridge = replace(bridge, structure_type="RM")
    elif kind == "ambiguous":
        legacy.identity_rows = pd.concat([legacy.identity_rows, legacy.identity_rows.assign(codigo_respuesta=8)])
    elif kind == "missing_metadata":
        legacy.identity_rows = pd.DataFrame()
    else:
        legacy.identity_rows = legacy.identity_rows.assign(source_variable="other", codigo_respuesta=8)
    records, limitations = legacy_comparison_records_from_report(legacy, result, identity_bridge=bridge)
    assert not records
    assert limitations


def test_conflicting_canonical_ids_fail_closed():
    legacy, result, bridge = projection()
    result = replace(result, values=(replace(result.values[0], category_id="different"),))
    records, limitations = legacy_comparison_records_from_report(legacy, result, identity_bridge=bridge)
    assert not records and limitations


def test_unsupported_mention_scope_fails_closed():
    legacy, result, bridge = projection(structure="RM", mention=True)
    result = replace(result, bases=(replace(result.bases[0], provenance_refs=("m4_resolved_scope_type:OPTION_RU",)),))
    records, limitations = legacy_comparison_records_from_report(legacy, result, identity_bridge=bridge)
    assert not records and limitations


def test_changed_denominator_fails_closed():
    legacy, result, bridge = projection()
    legacy.summary["base"] += 1
    records, limitations = legacy_comparison_records_from_report(legacy, result, identity_bridge=bridge)
    assert not records and limitations


def materialized(filters=None, banner=None):
    result = canonical_result()
    filters = {} if filters is None else filters
    banner = {} if banner is None else banner
    request = replace(result.request, filters=filters, banner_config=banner, compatibility_profile="CANONICAL_MATERIALIZATION_V1")
    refs = tuple(f"{ref}:{'|'.join(members)}" for ref, members in filters.items())
    if banner:
        slices = tuple(replace(result.slices[0], slice_id=f"slice-{member}", is_total=False, banner_dimension_id="physical-dimension", member_id=member, filter_refs=refs, configuration={"banner_ref": banner["banner_ref"], "raw_value": index}) for index, member in enumerate(banner["member_ids"]))
    else:
        slices = (replace(result.slices[0], is_total=not filters, banner_dimension_id=None, member_id=None, filter_refs=refs, configuration={"filters": refs} if filters else {"scope": "TOTAL"}),)
    return replace(result, request=request, slices=slices)


def bind(result):
    r = result.request
    return validate_request_binding(result, WebCanonicalRequest(r.question_ids, r.metric_refs, r.filters, r.banner_config, r.weight_override, r.execution_options))


def test_materialized_filter_preserves_slice_and_universe():
    result = materialized({"released-filter": ("member",)})
    assert bind(result) is result
    assert result.slices[0].filter_refs == ("released-filter:member",)
    assert not result.slices[0].is_total


@pytest.mark.parametrize("kind", ["scalar", "missing_id", "duplicate", "unsupported", "contradiction", "unfiltered"])
def test_materialized_filter_fail_closed(kind):
    result = materialized({"released-filter": ("member",)})
    if kind in {"scalar", "missing_id", "duplicate", "unsupported"}:
        filters = {"released-filter": "member"} if kind == "scalar" else {"": ("member",)} if kind == "missing_id" else {"released-filter": ("member", "member")} if kind == "duplicate" else {"released-filter": {"op": "unsupported"}}
        result = replace(result, request=replace(result.request, filters=filters))
    else:
        result = replace(result, slices=(replace(result.slices[0], filter_refs=() if kind == "unfiltered" else ("released-filter:other",)),))
    with pytest.raises(CanonicalRequestBindingError):
        bind(result)


def test_materialized_banner_preserves_identity_and_order():
    result = materialized(banner={"banner_ref": "released-banner", "member_ids": ["a", "b"]})
    assert bind(result) is result
    assert [s.member_id for s in result.slices] == ["a", "b"]


@pytest.mark.parametrize("kind", ["malformed", "missing_id", "unresolved", "duplicate", "wrong_banner", "wrong_order", "missing_raw", "unsupported", "conflicting_dimension", "duplicate_raw"])
def test_materialized_banner_fail_closed(kind):
    result = materialized(banner={"banner_ref": "released-banner", "member_ids": ["a", "b"]})
    if kind in {"malformed", "missing_id", "duplicate", "unsupported"}:
        banner = {"banner_ref": "released-banner", "member_ids": "a"} if kind == "malformed" else {"member_ids": ["a"]} if kind == "missing_id" else {"banner_ref": "released-banner", "member_ids": ["a", "a"]} if kind == "duplicate" else {"banner_ref": "released-banner", "member_ids": ["a"], "operation": "unknown"}
        result = replace(result, request=replace(result.request, banner_config=banner))
    elif kind == "unresolved":
        result = replace(result, slices=result.slices[:1])
    elif kind == "wrong_order":
        result = replace(result, slices=result.slices[::-1])
    else:
        first = result.slices[0]
        first = replace(first, banner_dimension_id="other") if kind == "conflicting_dimension" else replace(first, configuration={"banner_ref": "released-banner", "raw_value": 1}) if kind == "duplicate_raw" else replace(first, configuration={"banner_ref": "other", "raw_value": 0} if kind == "wrong_banner" else {"banner_ref": "released-banner"})
        result = replace(result, slices=(first, result.slices[1]))
    with pytest.raises(CanonicalRequestBindingError):
        bind(result)


def test_materialized_observability_records_actual_required_slices():
    result = materialized(banner={"banner_ref": "released-banner", "member_ids": ["a", "b"]})
    r = result.request
    request = WebCanonicalRequest(r.question_ids, r.metric_refs, r.filters, r.banner_config, r.weight_override, r.execution_options)
    metadata = request_observability(request, result)
    assert metadata["derived_required_slice_ids"] == ("slice-a", "slice-b")
    assert metadata["derived_required_slice_descriptors"] == ("materialized[slice-a]", "materialized[slice-b]")
