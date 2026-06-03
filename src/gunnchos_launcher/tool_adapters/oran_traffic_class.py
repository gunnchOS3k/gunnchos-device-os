import yaml
from pathlib import Path
def export(site_id: str = "gary") -> Path:
    out = Path("results/tool_exports/oran_traffic_classes.yaml")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.dump({"site_id": site_id, "classes": ["education", "general", "emergency"]}), encoding="utf-8")
    return out
