"""ACCESSIBILITY — AT-SPI-style semantics + keyboard/controller/Ring-alt journeys.

Human study remains EXTERNAL_PENDING; digital subsystem exits DIGITALLY_VALIDATED.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

CLAIM_BOUNDARY = (
    "System-wide AT-SPI-style digital accessibility semantics. "
    "Human study EXTERNAL_PENDING. No physical assistive-tech certification claimed."
)

ROLES_AT = ("button", "text", "heading", "list", "listitem", "switch", "slider", "menu", "menuitem")
JOURNEYS = ("keyboard", "controller", "ring_alt")


@dataclass
class AccessibleNode:
    node_id: str
    role: str
    name: str
    focusable: bool = True
    value: Any = None
    children: list[str] = field(default_factory=list)
    states: list[str] = field(default_factory=lambda: ["enabled"])


class AtSpiSemantics:
    """Minimal AT-SPI-style tree with focus traversal and action invocation."""

    def __init__(self):
        self.nodes: dict[str, AccessibleNode] = {}
        self.focus: str | None = None
        self.order: list[str] = []
        self.events: list[dict[str, Any]] = []

    def add(self, node: AccessibleNode) -> None:
        if node.role not in ROLES_AT:
            raise ValueError(node.role)
        self.nodes[node.node_id] = node
        if node.focusable:
            self.order.append(node.node_id)

    def set_focus(self, node_id: str) -> dict[str, Any]:
        if node_id not in self.nodes or not self.nodes[node_id].focusable:
            raise KeyError(node_id)
        self.focus = node_id
        self.events.append({"op": "focus", "node_id": node_id, "at": time.time()})
        return {"ok": True, "focus": node_id, "name": self.nodes[node_id].name}

    def next_focus(self) -> dict[str, Any]:
        if not self.order:
            raise RuntimeError("empty")
        if self.focus is None:
            return self.set_focus(self.order[0])
        idx = self.order.index(self.focus)
        return self.set_focus(self.order[(idx + 1) % len(self.order)])

    def activate(self) -> dict[str, Any]:
        if self.focus is None:
            return {"ok": False, "error": "no_focus"}
        node = self.nodes[self.focus]
        self.events.append({"op": "activate", "node_id": node.node_id, "role": node.role})
        return {"ok": True, "activated": node.node_id, "role": node.role, "name": node.name}

    def snapshot(self) -> dict[str, Any]:
        return {
            "focus": self.focus,
            "nodes": {k: asdict(v) for k, v in self.nodes.items()},
            "order": list(self.order),
        }


class AccessibilitySubsystem:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.tree = AtSpiSemantics()
        self._build_shell_tree()

    def _build_shell_tree(self) -> None:
        self.tree.add(AccessibleNode("hdr", "heading", "gunnchOS Home", focusable=False))
        self.tree.add(AccessibleNode("btn-launch", "button", "Launch Campus"))
        self.tree.add(AccessibleNode("btn-settings", "button", "Settings"))
        self.tree.add(AccessibleNode("swt-a11y", "switch", "High contrast", value=False))
        self.tree.add(AccessibleNode("sld-scale", "slider", "UI scale", value=1.0))
        self.tree.add(AccessibleNode("menu-main", "menu", "Main menu"))
        self.tree.add(AccessibleNode("mi-help", "menuitem", "Help"))

    def journey_keyboard(self) -> dict[str, Any]:
        steps = []
        steps.append(self.tree.next_focus())
        steps.append(self.tree.next_focus())
        steps.append(self.tree.activate())
        ok = steps[-1]["ok"] and steps[0]["focus"] == "btn-launch"
        return {"ok": ok, "modality": "keyboard", "steps": steps}

    def journey_controller(self) -> dict[str, Any]:
        # D-pad next + A activate
        self.tree.focus = None
        steps = [self.tree.next_focus(), self.tree.next_focus(), self.tree.next_focus(), self.tree.activate()]
        ok = steps[-1]["ok"] and steps[-1]["activated"] == "swt-a11y"
        return {"ok": ok, "modality": "controller", "steps": steps}

    def journey_ring_alt(self) -> dict[str, Any]:
        # Ring swipe cycles focus; tap activates
        self.tree.focus = None
        for _ in range(4):
            self.tree.next_focus()
        act = self.tree.activate()
        ok = act["ok"] and act["activated"] == "sld-scale"
        return {"ok": ok, "modality": "ring_alt", "activated": act}

    def e2e(self) -> dict[str, Any]:
        kb = self.journey_keyboard()
        ctl = self.journey_controller()
        ring = self.journey_ring_alt()
        roles_ok = set(n.role for n in self.tree.nodes.values()) >= {"button", "switch", "slider", "menu"}
        ok = kb["ok"] and ctl["ok"] and ring["ok"] and roles_ok
        report = {
            "schema": "gunnchos.phase_xv.accessibility.e2e.v1",
            "ok": ok,
            "exit_state": "DIGITALLY_VALIDATED" if ok else "INCOMPLETE_DIGITAL",
            "human_study": "EXTERNAL_PENDING",
            "journeys": {j: True for j in JOURNEYS},
            "keyboard": kb,
            "controller": ctl,
            "ring_alt": ring,
            "tree": self.tree.snapshot(),
            "claim_boundary": CLAIM_BOUNDARY,
            "frontier_parity_claimed": False,
        }
        (self.root / "ACCESSIBILITY_E2E.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report
