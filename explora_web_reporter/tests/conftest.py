from __future__ import annotations

from pathlib import Path
import sys


# Ensure direct `pytest` execution from explora_web_reporter can import the
# application package as `src`, matching normal Streamlit/runtime execution.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)
if PROJECT_ROOT_TEXT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_TEXT)

def pytest_configure(config) -> None:
    """Use a repository-local pytest temp root when Windows TEMP is inaccessible."""
    if getattr(config.option, "basetemp", None):
        return
    local_temp = PROJECT_ROOT / ".pytest_tmp_gate48"
    local_temp.mkdir(parents=True, exist_ok=True)
    config.option.basetemp = local_temp
