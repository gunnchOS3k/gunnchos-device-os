"""Map CX4 Edmund action packet into Validation Center task library."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from gunnchos_device_os.cx4_validation_center.library import build_task_library


def parse_edmund_packet(text: str) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []
    blocks = re.split(r"\n##\s+", text)
    for block in blocks:
        m = re.match(r"(\d+)\)\s+(.+)", block.strip())
        if not m:
            continue
        body = block
        def _field(label: str) -> str:
            mm = re.search(rf"\*\*{label}:\*\*\s*(.+)", body)
            return (mm.group(1).strip() if mm else "")

        actions.append(
            {
                "edmund_action_id": m.group(1),
                "title": m.group(2).strip(),
                "steps": _field("Steps"),
                "estimate": _field("Estimate"),
                "prerequisite": _field("Prerequisite"),
                "evidence": _field("Evidence"),
                "unlocks": _field("Unlocks"),
            }
        )
    return actions


def map_edmund_to_tasks(packet_path: Path | None = None) -> Dict[str, Any]:
    if packet_path is None:
        # default relative to repo
        here = Path(__file__).resolve()
        packet_path = here.parents[2] / "docs" / "complete-experience" / "cx4_readiness" / "CX4_EDMUND_ACTION_PACKET.md"
    text = packet_path.read_text(encoding="utf-8") if packet_path.is_file() else ""
    actions = parse_edmund_packet(text) if text else []
    tasks = build_task_library()
    mapped = []
    for action in actions:
        matches = [t for t in tasks if t.edmund_action_id == action["edmund_action_id"]]
        mapped.append(
            {
                "edmund_action_id": action["edmund_action_id"],
                "title": action["title"],
                "prerequisite": action["prerequisite"],
                "estimated_time": action["estimate"],
                "required_equipment_or_person": action.get("steps", ""),
                "exact_evidence": action["evidence"],
                "gate_unlocked": action["unlocks"],
                "task_ids": [t.task_id for t in matches],
                "ui_visible": True,
            }
        )
    # Ensure markdown packet remains and mapping covers all numbered actions found
    all_mapped = bool(actions) and all(m["task_ids"] for m in mapped if m["edmund_action_id"] != "10")
    # Action 10 is WAIKE release dependency — map as pending external informational
    for m in mapped:
        if m["edmund_action_id"] == "10" and not m["task_ids"]:
            m["task_ids"] = []
            m["ui_visible"] = True
            m["status"] = "pending_external_dependency"
            m["note"] = "WAIKE release dependency — do not modify release; not a VC executable task."
    return {
        "packet_path": str(packet_path),
        "packet_exists": packet_path.is_file(),
        "actions": mapped,
        "CX4_EDMUND_ACTION_PACKET_UI_MAPPED": bool(packet_path.is_file() and mapped and all_mapped),
        "markdown_preserved": True,
    }
