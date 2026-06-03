from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from security.sbom import generate_spdx


def test_generate_spdx(tmp_path):
    out = tmp_path / "test.spdx.json"
    generate_spdx(out)
    data = json.loads(out.read_text())
    assert data["spdxVersion"] == "2.3"
