from pathlib import Path
import yaml

DIR = Path(__file__).resolve().parents[2] / "configs" / "campus_device_modes"


def list_campuses() -> list[str]:
    return sorted(p.stem for p in DIR.glob("*.yaml"))


def load_mode(site_id: str) -> dict:
    with (DIR / f"{site_id}.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)
