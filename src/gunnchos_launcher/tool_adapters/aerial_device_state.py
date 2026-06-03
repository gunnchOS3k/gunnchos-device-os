import json
from pathlib import Path
def export(site_id: str = "gary") -> Path:
    out = Path("results/tool_exports/aerial_device_state.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"site_id": site_id, "evidence_status": "stub"}, indent=2) + "\n", encoding="utf-8")
    return out
