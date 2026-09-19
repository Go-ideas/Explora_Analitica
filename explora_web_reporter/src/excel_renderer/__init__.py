"""Contract-driven canonical Excel presentation; no analytical execution."""
from .renderer import (
    MasterManifest, RenderError, RenderPlan, RenderRequest, Slot, TableBinding,
    plan_render, render, validate_output,
)
from .qualification import QualifiedMaster, load_qualified_master, vba_sha256
from .production import benchmark_a_request

__all__ = ["MasterManifest", "QualifiedMaster", "RenderError", "RenderPlan", "RenderRequest",
           "Slot", "TableBinding", "load_qualified_master", "plan_render", "render",
           "benchmark_a_request", "validate_output", "vba_sha256"]
