import pandas as pd
import pytest

from src.readers.datamap_reader import _merge_source_by_variable


@pytest.mark.parametrize("infer_string", [False, True])
def test_metadata_merge_preserves_boolean_numeric_and_existing_values(infer_string):
    with pd.option_context("future.infer_string", infer_string):
        source = pd.DataFrame({
            "Variable": ["alpha", "beta", "gamma"],
            "Enabled": ["", "No", ""],
            "Code": ["", "kept", ""],
        })
        metadata = pd.DataFrame({
            "Variable": ["gamma", "beta", "alpha"],
            "Enabled": [False, True, True],
            "Code": [0, 9, 12],
            "Extra": [False, True, True],
        })
        merged = _merge_source_by_variable(source, metadata)
        assert merged["Enabled"].tolist() == [True, "No", False]
        assert merged["Code"].tolist() == [12, "kept", 0]
        assert merged["Extra"].tolist() == [True, True, False]
        assert source["Enabled"].tolist() == ["", "No", ""]
