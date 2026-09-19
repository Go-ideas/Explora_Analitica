"""Contract-driven canonical Excel presentation; no analytical execution."""
from .renderer import (
    MasterManifest, RenderError, RenderPlan, RenderRequest, Slot, TableBinding,
    plan_render, render, validate_output,
)

__all__ = ["MasterManifest", "RenderError", "RenderPlan", "RenderRequest", "Slot",
           "TableBinding", "plan_render", "render", "validate_output"]
