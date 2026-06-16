#!/usr/bin/env python3
"""Build an access graph from mock IAM fixtures and surface risky paths."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LAB_DIR = Path(__file__).resolve().parent

KNOWN_RISK_PATTERNS: dict[str, dict[str, str]] = {
    "guest_to_telemetry": {
        "title": "Guest reads fleet telemetry",
        "severity": "high",
        "description": "Untrusted demo guest can read telemetry outside the demo isolation zone.",
    },
    "service_agent_impersonate": {
        "title": "Service agent impersonation",
        "severity": "critical",
        "description": "Automation principal can assume an interactive student identity.",
    },
    "educator_over_export": {
        "title": "Educator bulk export",
        "severity": "high",
        "description": "Educator role can export all student learning records in bulk.",
    },
    "model_config_without_approval": {
        "title": "Model config write without approval",
        "severity": "critical",
        "description": "Research operator can mutate ML policy without an approval gate.",
    },
}


@dataclass
class AccessEdge:
    source: str
    target: str
    permission: str
    scope: str
    risk_tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessGraph:
    identities: dict[str, dict[str, Any]]
    resources: dict[str, dict[str, Any]]
    edges: list[AccessEdge]

    def risky_edges(self) -> list[AccessEdge]:
        return [edge for edge in self.edges if edge.risk_tags]

    def risky_paths(self) -> list[dict[str, Any]]:
        paths: list[dict[str, Any]] = []
        for edge in self.risky_edges():
            source = self.identities.get(edge.source, {"id": edge.source})
            target = self.resources.get(edge.target) or self.identities.get(
                edge.target, {"id": edge.target}
            )
            for tag in edge.risk_tags:
                pattern = KNOWN_RISK_PATTERNS.get(tag, {})
                paths.append(
                    {
                        "risk_tag": tag,
                        "title": pattern.get("title", tag),
                        "severity": pattern.get("severity", "medium"),
                        "description": pattern.get("description", "Flagged by mock policy."),
                        "path": [edge.source, edge.target],
                        "permission": edge.permission,
                        "scope": edge.scope,
                        "source_role": source.get("role", "unknown"),
                        "target_sensitivity": target.get("sensitivity", "unknown"),
                    }
                )
        return paths


def load_json(name: str, base_dir: Path = LAB_DIR) -> dict[str, Any]:
    path = base_dir / name
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_graph(
    identities_doc: dict[str, Any],
    resources_doc: dict[str, Any],
    bindings_doc: dict[str, Any],
) -> AccessGraph:
    identities = {item["id"]: item for item in identities_doc["identities"]}
    resources = {item["id"]: item for item in resources_doc["resources"]}
    edges: list[AccessEdge] = []

    for binding in bindings_doc["bindings"]:
        edges.append(
            AccessEdge(
                source=binding["identity"],
                target=binding["resource"],
                permission=binding["permission"],
                scope=binding.get("scope", ""),
                risk_tags=list(binding.get("risk_tags", [])),
                metadata={
                    "approval_gate": binding.get("approval_gate"),
                },
            )
        )

    return AccessGraph(identities=identities, resources=resources, edges=edges)


def render_report(graph: AccessGraph) -> str:
    paths = graph.risky_paths()
    lines = [
        "# gunnchOS Access Risk Report (Example)",
        "",
        "Defensive lab output generated from mock identities, resources, and IAM bindings.",
        "No live credentials or tenant data are used.",
        "",
        "## Summary",
        "",
        f"- Identities modeled: **{len(graph.identities)}**",
        f"- Resources modeled: **{len(graph.resources)}**",
        f"- IAM bindings modeled: **{len(graph.edges)}**",
        f"- Risky paths detected: **{len(paths)}**",
        "",
        "## Risky Access Paths",
        "",
    ]

    if not paths:
        lines.append("_No risky paths detected in the mock graph._")
        return "\n".join(lines) + "\n"

    for index, path in enumerate(paths, start=1):
        lines.extend(
            [
                f"### {index}. {path['title']} (`{path['risk_tag']}`)",
                "",
                f"- **Severity:** {path['severity']}",
                f"- **Path:** `{path['path'][0]}` → `{path['path'][1]}`",
                f"- **Permission:** `{path['permission']}` (`{path['scope']}`)",
                f"- **Source role:** `{path['source_role']}`",
                f"- **Target sensitivity:** `{path['target_sensitivity']}`",
                f"- **Rationale:** {path['description']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Recommended Next Steps",
            "",
            "1. Run `least_privilege_recommender.py` for downgrade suggestions.",
            "2. Add approval gates for privileged automation and research mutations.",
            "3. Isolate demo guests from fleet telemetry and student data planes.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(graph: AccessGraph, output_path: Path | None = None) -> Path:
    destination = output_path or (LAB_DIR / "risk_report_example.md")
    destination.write_text(render_report(graph), encoding="utf-8")
    return destination


def analyze(base_dir: Path = LAB_DIR) -> tuple[AccessGraph, Path]:
    graph = build_graph(
        load_json("sample_identities.json", base_dir),
        load_json("sample_resources.json", base_dir),
        load_json("sample_iam_bindings.json", base_dir),
    )
    report_path = write_report(graph, base_dir / "risk_report_example.md")
    return graph, report_path


def main() -> None:
    graph, report_path = analyze()
    risky_count = len(graph.risky_paths())
    print(f"Built graph with {len(graph.edges)} edges and {risky_count} risky paths.")
    print(f"Wrote report to {report_path}")


if __name__ == "__main__":
    main()
