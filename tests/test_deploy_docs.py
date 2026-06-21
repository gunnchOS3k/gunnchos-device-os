"""Tests deploy diagram docs exist."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_deploy_docs_and_diagrams():
    docs = [
        "docs/LOCAL_WIFI_USBC_DEPLOY_FLOW.md",
        "docs/DEPLOY_FLOW_DIAGRAMS.md",
        "diagrams/deploy_flow_local_wifi.mmd",
        "diagrams/deploy_flow_usbc.mmd",
        "diagrams/deploy_flow_offline_bundle.mmd",
    ]
    for rel in docs:
        assert (ROOT / rel).exists(), rel
        content = (ROOT / rel).read_text(encoding="utf-8")
        assert len(content) > 50
