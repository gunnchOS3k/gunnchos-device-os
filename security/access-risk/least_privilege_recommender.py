#!/usr/bin/env python3
"""Recommend least-privilege downgrades for mock IAM bindings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LAB_DIR = Path(__file__).resolve().parent

RECOMMENDATIONS: dict[str, dict[str, str]] = {
    "guest_to_telemetry": {
        "risk": "high",
        "recommended_permission": "deny",
        "rationale": "Demo guests must stay inside the public sandbox; telemetry is fleet-scoped.",
    },
    "service_agent_impersonate": {
        "risk": "critical",
        "recommended_permission": "impersonate_with_break_glass_approval",
        "rationale": "Support automation should require time-bound approval and audit before identity takeover.",
    },
    "educator_over_export": {
        "risk": "high",
        "recommended_permission": "export_class_scope_with_audit",
        "rationale": "Replace bulk export with class-scoped export, watermarking, and audit events.",
    },
    "model_config_without_approval": {
        "risk": "critical",
        "recommended_permission": "write_with_dual_control",
        "rationale": "Model policy changes should require research lead approval and change tickets.",
    },
}

DEFAULT_RECOMMENDATION = {
    "risk": "low",
    "recommended_permission": "keep",
    "rationale": "Binding matches expected role baseline for the mock lab.",
}


def load_bindings(base_dir: Path = LAB_DIR) -> list[dict[str, Any]]:
    document = json.loads((base_dir / "sample_iam_bindings.json").read_text(encoding="utf-8"))
    return document["bindings"]


def recommend_for_binding(binding: dict[str, Any]) -> dict[str, str]:
    tags = binding.get("risk_tags", [])
    for tag in tags:
        if tag in RECOMMENDATIONS:
            return RECOMMENDATIONS[tag]
    if binding.get("permission") == "write" and binding.get("approval_gate") is False:
        return RECOMMENDATIONS["model_config_without_approval"]
    return DEFAULT_RECOMMENDATION


def generate_recommendations(
    bindings: list[dict[str, Any]] | None = None,
    base_dir: Path = LAB_DIR,
) -> list[dict[str, str]]:
    bindings = bindings if bindings is not None else load_bindings(base_dir)
    rows: list[dict[str, str]] = []
    for binding in bindings:
        recommendation = recommend_for_binding(binding)
        rows.append(
            {
                "identity": binding["identity"],
                "resource": binding["resource"],
                "current_permission": f"{binding['permission']} ({binding.get('scope', '')})",
                "risk": recommendation["risk"],
                "recommended_permission": recommendation["recommended_permission"],
                "rationale": recommendation["rationale"],
            }
        )
    return rows


def format_markdown_table(rows: list[dict[str, str]]) -> str:
    header = (
        "| Identity | Resource | Current Permission | Risk | "
        "Recommended Permission | Rationale |"
    )
    separator = "| --- | --- | --- | --- | --- | --- |"
    body = [
        "| {identity} | {resource} | {current_permission} | {risk} | "
        "{recommended_permission} | {rationale} |".format(**row)
        for row in rows
    ]
    lines = [
        "# Least Privilege Recommendations (Mock Lab)",
        "",
        "Generated from `sample_iam_bindings.json`. Educational output only.",
        "",
        header,
        separator,
        *body,
        "",
    ]
    return "\n".join(lines)


def write_recommendations(
    output_path: Path | None = None,
    base_dir: Path = LAB_DIR,
) -> Path:
    destination = output_path or (base_dir / "least_privilege_recommendations.md")
    rows = generate_recommendations(base_dir=base_dir)
    destination.write_text(format_markdown_table(rows), encoding="utf-8")
    return destination


def main() -> None:
    destination = write_recommendations()
    rows = generate_recommendations()
    risky = sum(1 for row in rows if row["risk"] != "low")
    print(f"Generated {len(rows)} recommendations ({risky} non-low risk).")
    print(f"Wrote table to {destination}")


if __name__ == "__main__":
    main()
