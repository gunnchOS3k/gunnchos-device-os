import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from update_system.manifest import sample_manifest
from update_system.rollback import rollback_available


def test_manifest_and_rollback():
    m = sample_manifest()
    assert m["version"]
    assert rollback_available()
