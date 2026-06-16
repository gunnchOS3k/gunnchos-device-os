"""Tests for gunnchOS Access Risk Intelligence Lab (mock data only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LAB_DIR = REPO_ROOT / "security" / "access-risk"
sys.path.insert(0, str(LAB_DIR))

from attack_path_model import analyze, build_graph, load_json  # noqa: E402
from least_privilege_recommender import (  # noqa: E402
    format_markdown_table,
    generate_recommendations,
    load_bindings,
)


@pytest.fixture
def lab_docs():
    return (
        load_json("sample_identities.json", LAB_DIR),
        load_json("sample_resources.json", LAB_DIR),
        load_json("sample_iam_bindings.json", LAB_DIR),
    )


def test_graph_builds_from_mock_fixtures(lab_docs):
    identities, resources, bindings = lab_docs
    graph = build_graph(identities, resources, bindings)

    assert len(graph.identities) == 5
    assert len(graph.resources) == 6
    assert len(graph.edges) == len(bindings["bindings"])
    assert graph.identities["student_user"]["role"] == "student"
    assert graph.resources["telemetry_bucket"]["zone"] == "fleet_ops"


def test_risky_paths_detected(lab_docs):
    identities, resources, bindings = lab_docs
    graph = build_graph(identities, resources, bindings)
    paths = graph.risky_paths()
    tags = {path["risk_tag"] for path in paths}

    assert len(paths) >= 4
    assert "guest_to_telemetry" in tags
    assert "service_agent_impersonate" in tags
    assert "educator_over_export" in tags
    assert "model_config_without_approval" in tags


def test_recommendations_generated():
    rows = generate_recommendations(base_dir=LAB_DIR)

    assert len(rows) == len(load_bindings(LAB_DIR))
    risky_rows = [row for row in rows if row["risk"] != "low"]
    assert len(risky_rows) >= 4

    table = format_markdown_table(rows)
    assert "| Identity | Resource |" in table
    assert "public_demo_guest" in table
    assert "deny" in table


def test_analyze_writes_report(tmp_path):
    graph, report_path = analyze(base_dir=LAB_DIR)
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "Risky Access Paths" in content
    assert len(graph.risky_paths()) >= 4


def test_no_secrets_required_in_fixtures():
    for name in (
        "sample_identities.json",
        "sample_resources.json",
        "sample_iam_bindings.json",
    ):
        document = json.loads((LAB_DIR / name).read_text(encoding="utf-8"))
        serialized = json.dumps(document).lower()
        for forbidden in ("api_key", "password", "secret", "token", "credential"):
            assert forbidden not in serialized
