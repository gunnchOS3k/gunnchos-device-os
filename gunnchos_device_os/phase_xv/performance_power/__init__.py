"""PERFORMANCE_POWER — digital policy/budgets/cgroups/QoS.

After digital work is exhausted, exit PHYSICAL_PENDING (do not fake DIGITALLY_VALIDATED
for physical thermal/power metrics). EVT handoff tests are documented in artifacts.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

CLAIM_BOUNDARY = (
    "Digital performance/power policy, budgets, cgroups, and QoS only. "
    "Physical thermal/FPS/battery metrics PHYSICAL_PENDING — not digitally validated."
)

PROFILES = ("handheld_game", "student_desk", "dsxl_dev", "powersave", "balanced")


@dataclass
class Budget:
    name: str
    cpu_pct: int
    mem_mb: int
    io_weight: int
    thermal_hint: str  # policy hint only; not measured


@dataclass
class CgroupSlice:
    name: str
    cpu_max: str
    memory_max: str
    io_weight: int


class PerformancePowerPolicy:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.budgets = {
            "handheld_game": Budget("handheld_game", 85, 4500, 800, "sustain_perf"),
            "student_desk": Budget("student_desk", 70, 6000, 500, "quiet"),
            "dsxl_dev": Budget("dsxl_dev", 95, 12000, 900, "sustained"),
            "powersave": Budget("powersave", 35, 2500, 200, "cool"),
            "balanced": Budget("balanced", 60, 4000, 400, "balanced"),
        }
        self.qos_classes = ("realtime_ui", "interactive", "best_effort", "idle")
        self.active_profile = "balanced"
        self.slices: list[CgroupSlice] = []

    def apply_profile(self, profile: str) -> dict[str, Any]:
        if profile not in self.budgets:
            raise ValueError(profile)
        self.active_profile = profile
        b = self.budgets[profile]
        self.slices = [
            CgroupSlice("ui.slice", f"{b.cpu_pct * 1000}/100ms", f"{int(b.mem_mb * 0.35)}M", b.io_weight),
            CgroupSlice("apps.slice", f"{int(b.cpu_pct * 0.7) * 1000}/100ms", f"{int(b.mem_mb * 0.45)}M", max(100, b.io_weight - 100)),
            CgroupSlice("bg.slice", "20%/100ms", f"{int(b.mem_mb * 0.15)}M", 100),
        ]
        return {"ok": True, "profile": profile, "budget": asdict(b), "slices": [asdict(s) for s in self.slices]}

    def qos_schedule(self, workloads: list[dict[str, str]]) -> dict[str, Any]:
        ranked = {c: [] for c in self.qos_classes}
        for w in workloads:
            cls = w.get("qos", "best_effort")
            if cls not in ranked:
                cls = "best_effort"
            ranked[cls].append(w["name"])
        order = [n for c in self.qos_classes for n in ranked[c]]
        return {"ok": True, "order": order, "ranked": ranked}

    def write_evt_handoff(self) -> Path:
        out = self.root / "EVT_PERFORMANCE_POWER_HANDOFF.md"
        out.write_text(
            "\n".join(
                [
                    "# EVT handoff — PERFORMANCE_POWER",
                    "",
                    "Digital policy/budgets/cgroups/QoS are complete under PHYSICAL_EXECUTION_FREEZE.",
                    "Physical validation required on EVT boards (do **not** claim DIGITALLY_VALIDATED for these):",
                    "",
                    "1. Sustained CPU package power vs budget under handheld_game / dsxl_dev profiles",
                    "2. Skin/SoC thermals with thermal_hint policy applied (throttling curves)",
                    "3. Battery discharge rate (Handheld) across powersave vs balanced",
                    "4. Frame-time / jank under UI realtime_qos with compositor load",
                    "5. cgroup enforcement observed via systemd-cgtop / cgget on target image",
                    "",
                    "Exit for Phase XV digital gate: **PHYSICAL_PENDING** after digital work exhausted.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return out

    def e2e(self) -> dict[str, Any]:
        applied = {}
        for p in PROFILES:
            applied[p] = self.apply_profile(p)["ok"]
        qos = self.qos_schedule(
            [
                {"name": "shell", "qos": "realtime_ui"},
                {"name": "browser", "qos": "interactive"},
                {"name": "sync", "qos": "best_effort"},
                {"name": "indexer", "qos": "idle"},
            ]
        )
        handoff = self.write_evt_handoff()
        digital_ok = all(applied.values()) and qos["ok"] and handoff.exists() and len(self.slices) == 3
        # Intentional: gate exit is PHYSICAL_PENDING once digital policy is complete.
        return {
            "schema": "gunnchos.phase_xv.performance_power.e2e.v1",
            "ok": digital_ok,
            "exit_state": "PHYSICAL_PENDING" if digital_ok else "INCOMPLETE_DIGITAL",
            "digital_policy_complete": digital_ok,
            "profiles": list(PROFILES),
            "qos_classes": list(self.qos_classes),
            "applied": applied,
            "qos": qos,
            "evt_handoff": handoff.name,
            "physical_metrics_claimed": False,
            "claim_boundary": CLAIM_BOUNDARY,
            "frontier_parity_claimed": False,
        }
