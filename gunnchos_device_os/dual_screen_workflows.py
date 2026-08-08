"""Dual-screen app workflow stubs with per-type validation.

Extends the DS-XL dual-screen framework with explicit workflow types
(coder/debug/docs/terminal/pair) and automated validators. Software
role model only — not a compositor.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from gunnchos_device_os.dual_screen import (
    CLAIM_BOUNDARY,
    DEFAULT_WORKFLOWS,
    DualScreenFramework,
    ScreenId,
)


@dataclass(frozen=True)
class WorkflowTypeSpec:
    name: str
    description: str
    required_roles: frozenset[str]
    top_role: str
    bottom_role: str
    app_stubs: tuple[str, ...]


WORKFLOW_TYPES: dict[str, WorkflowTypeSpec] = {
    "coder": WorkflowTypeSpec(
        name="coder",
        description="Code on top, live preview on bottom",
        required_roles=frozenset({"code", "preview"}),
        top_role="code",
        bottom_role="preview",
        app_stubs=("editor", "preview_pane"),
    ),
    "debug": WorkflowTypeSpec(
        name="debug",
        description="Code on top, debugger on bottom",
        required_roles=frozenset({"code", "debug"}),
        top_role="code",
        bottom_role="debug",
        app_stubs=("editor", "debugger"),
    ),
    "docs": WorkflowTypeSpec(
        name="docs",
        description="Docs on top, code on bottom",
        required_roles=frozenset({"docs", "code"}),
        top_role="docs",
        bottom_role="code",
        app_stubs=("docs_viewer", "editor"),
    ),
    "terminal": WorkflowTypeSpec(
        name="terminal",
        description="Code on top, terminal on bottom",
        required_roles=frozenset({"code", "terminal"}),
        top_role="code",
        bottom_role="terminal",
        app_stubs=("editor", "terminal"),
    ),
    "pair": WorkflowTypeSpec(
        name="pair",
        description="Code on top, chat/pair pane on bottom",
        required_roles=frozenset({"code", "chat"}),
        top_role="code",
        bottom_role="chat",
        app_stubs=("editor", "pair_chat"),
    ),
}


@dataclass
class WorkflowValidationResult:
    workflow: str
    ok: bool
    checks: list[dict[str, Any]] = field(default_factory=list)
    layout: dict[str, Any] = field(default_factory=dict)
    claim_boundary: str = CLAIM_BOUNDARY

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow": self.workflow,
            "ok": self.ok,
            "checks": list(self.checks),
            "layout": dict(self.layout),
            "claim_boundary": self.claim_boundary,
            "mock": False,
        }


def _check(name: str, passed: bool, detail: str = "") -> dict[str, Any]:
    return {"check": name, "ok": passed, "detail": detail}


def validate_workflow(fw: DualScreenFramework, name: str) -> WorkflowValidationResult:
    if name not in WORKFLOW_TYPES:
        raise ValueError(f"unknown workflow type: {name}")
    spec = WORKFLOW_TYPES[name]
    if fw.active_workflow != name:
        fw.apply_workflow(name)
    layout = fw.layout()
    top_role = layout["top"]["role"]
    bottom_role = layout["bottom"]["role"]
    checks = [
        _check("workflow_active", fw.active_workflow == name, fw.active_workflow or ""),
        _check("top_role", top_role == spec.top_role, f"{top_role}=={spec.top_role}"),
        _check("bottom_role", bottom_role == spec.bottom_role, f"{bottom_role}=={spec.bottom_role}"),
        _check(
            "required_roles_present",
            {top_role, bottom_role} >= set(spec.required_roles),
            f"{top_role},{bottom_role}",
        ),
        _check("focus_exactly_one", "focus_must_be_exactly_one" not in fw.validate_roles()),
        _check("not_both_empty", "both_screens_empty" not in fw.validate_roles()),
        _check("matches_default_map", DEFAULT_WORKFLOWS[name][ScreenId.TOP.value].value == top_role),
    ]
    return WorkflowValidationResult(
        workflow=name,
        ok=all(c["ok"] for c in checks),
        checks=checks,
        layout=layout,
    )


def place_app_stubs(fw: DualScreenFramework, name: str) -> dict[str, Any]:
    """Place deterministic app stubs for a workflow type without clearing workflow."""
    spec = WORKFLOW_TYPES[name]
    fw.apply_workflow(name)
    top_app, bottom_app = spec.app_stubs
    fw.screens[ScreenId.TOP.value].app_id = top_app
    fw.screens[ScreenId.BOTTOM.value].app_id = bottom_app
    fw.focus(ScreenId.TOP)
    # focus() snapshots but does not clear active_workflow
    return {
        "workflow": name,
        "apps": {"top": top_app, "bottom": bottom_app},
        "layout": fw.layout(),
        "validation": validate_workflow(fw, name).to_dict(),
    }


def run_all_workflow_validations() -> dict[str, Any]:
    fw = DualScreenFramework()
    results = []
    for name in sorted(WORKFLOW_TYPES.keys()):
        place_app_stubs(fw, name)
        results.append(validate_workflow(fw, name).to_dict())
    ok = all(r["ok"] for r in results)
    return {
        "schema": "gunnchos.dual_screen.workflow_validation.v1",
        "ok": ok,
        "workflow_count": len(results),
        "results": results,
        "token": "GUNNCHOS_DUAL_SCREEN_WORKFLOW_DIGITAL_PASS" if ok else None,
        "claim_boundary": CLAIM_BOUNDARY,
        "full_operational_product_claimed": False,
    }


VALIDATORS: dict[str, Callable[[DualScreenFramework], WorkflowValidationResult]] = {
    name: (lambda fw, n=name: validate_workflow(fw, n)) for name in WORKFLOW_TYPES
}
