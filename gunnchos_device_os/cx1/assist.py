"""CX1I Assist — accessibility digital paths; HUMAN_A11Y_PENDING for human verification."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from gunnchos_device_os.cx0.accessibility_inventory import export_accessibility_inventory


@dataclass
class FocusNode:
    id: str
    role: str
    label: str
    order: int

    def to_dict(self) -> dict:
        return {"id": self.id, "role": self.role, "label": self.label, "order": self.order}


@dataclass
class Assist:
    root: Path
    high_contrast: bool = False
    reduce_motion: bool = False
    ui_scale: float = 1.0
    keyboard_only: bool = True
    focus_order: List[FocusNode] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.focus_order = [
            FocusNode("home", "landmark", "gunnch Home", 1),
            FocusNode("vault", "button", "Vault", 2),
            FocusNode("app_center", "button", "App Center", 3),
            FocusNode("connect", "button", "Connect", 4),
            FocusNode("assist", "button", "Assist", 5),
            FocusNode("care", "button", "Care", 6),
        ]
        self._save()

    def _save(self) -> None:
        (self.root / "assist_state.json").write_text(
            json.dumps(
                {
                    "high_contrast": self.high_contrast,
                    "reduce_motion": self.reduce_motion,
                    "ui_scale": self.ui_scale,
                    "keyboard_only": self.keyboard_only,
                    "focus_order": [n.to_dict() for n in self.focus_order],
                },
                indent=2,
            )
            + "\n"
        )

    def set_high_contrast(self, enabled: bool) -> dict:
        self.high_contrast = enabled
        self._save()
        return {"high_contrast": enabled, "evidence_class": "DIGITAL_A11Y_PASS"}

    def set_reduce_motion(self, enabled: bool) -> dict:
        self.reduce_motion = enabled
        self._save()
        return {"reduce_motion": enabled, "evidence_class": "DIGITAL_A11Y_PASS"}

    def set_scale(self, scale: float) -> dict:
        if scale < 0.75 or scale > 3.0:
            raise ValueError("scale_out_of_range")
        self.ui_scale = scale
        self._save()
        return {"ui_scale": scale, "evidence_class": "DIGITAL_A11Y_PASS"}

    def keyboard_journey(self, stops: List[str] | None = None) -> dict:
        stops = stops or ["home", "vault", "app_center", "care"]
        ids = [n.id for n in sorted(self.focus_order, key=lambda n: n.order)]
        visited = []
        for stop in stops:
            if stop not in ids:
                return {
                    "ok": False,
                    "missing": stop,
                    "evidence_class": "DIGITAL_PARTIAL",
                }
            visited.append(stop)
        # semantics: every stop has label+role
        semantics = [
            n.to_dict()
            for n in self.focus_order
            if n.id in stops and n.label and n.role
        ]
        return {
            "ok": len(visited) == len(stops) and len(semantics) == len(stops),
            "visited": visited,
            "semantics": semantics,
            "evidence_class": "DIGITAL_A11Y_PASS",
            "human_verification": "HUMAN_A11Y_PENDING",
            "claim_boundary": "digital_semantics_not_human_a11y_pass",
        }

    def atspi_discovery(self) -> dict:
        atspi = shutil.which("atk-bridge") or shutil.which("accerciser")
        return {
            "atspi_available": bool(atspi),
            "binary": atspi,
            "evidence_class": "DIGITAL_A11Y_PASS" if atspi else "DIGITAL_PARTIAL",
            "human_verification": "HUMAN_A11Y_PENDING",
        }

    def tts_stt_discovery(self) -> dict:
        tts = shutil.which("espeak") or shutil.which("espeak-ng") or shutil.which("say")
        stt = shutil.which("whisper") or shutil.which("vosk")
        return {
            "tts": {"available": bool(tts), "binary": tts},
            "stt": {"available": bool(stt), "binary": stt},
            "evidence_class": "DIGITAL_PARTIAL",
            "human_verification": "HUMAN_A11Y_PENDING",
        }

    def switch_adaptive_discovery(self) -> dict:
        return {
            "switch_control": {"discovered": False, "notes": "hardware_pending"},
            "adaptive": {"discovered": False, "notes": "hardware_pending"},
            "evidence_class": "DIGITAL_PARTIAL",
            "human_verification": "HUMAN_A11Y_PENDING",
        }

    def captions_hooks(self) -> dict:
        return {
            "captions_hook": True,
            "wired": False,
            "notes": "hook_present_media_pipeline_HUMAN_PENDING",
            "evidence_class": "DIGITAL_PARTIAL",
        }

    def inventory(self, device_profile: str = "handheld_student") -> dict:
        base = export_accessibility_inventory(device_profile).to_dict()
        base["cx1"] = {
            "keyboard_only": self.keyboard_only,
            "high_contrast": self.high_contrast,
            "reduce_motion": self.reduce_motion,
            "ui_scale": self.ui_scale,
            "focus_order": [n.to_dict() for n in self.focus_order],
            "atspi": self.atspi_discovery(),
            "tts_stt": self.tts_stt_discovery(),
            "switch_adaptive": self.switch_adaptive_discovery(),
            "captions": self.captions_hooks(),
        }
        base["evidence_tier"] = "digital"
        base["human_verification"] = "HUMAN_A11Y_PENDING"
        return base
