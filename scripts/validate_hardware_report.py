#!/usr/bin/env python3
"""Validate reference hardware validation reports and matrix."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "hardware_validation" / "reference_device_matrix.yaml"
TEMPLATE = ROOT / "hardware_validation" / "reference_device_report.template.md"
EXAMPLE = ROOT / "hardware_validation" / "reference_device_report.example.md"

REQUIRED_SIGNOFF_KEYS = (
    "physical_validation_performed",
    "validation_environment",
    "approved_for_beta_hardware_claim",
    "container_only",
)

FORBIDDEN_CLAIMS = (
    "physical validation performed: yes",
    "physical hardware validation complete",
    "all devices physically validated",
    "hardware-validated across fleet",
    "approved for beta hardware claim: true",
)

CONTAINER_MARKERS = (
    "container only",
    "container_only: true",
    "validation_environment: container",
    "physical_validation_performed: false",
)


def _parse_signoff_yaml(text: str) -> dict[str, str | bool]:
    """Extract fenced yaml sign-off block from markdown report."""
    match = re.search(r"```yaml\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if not match:
        return {}
    block = yaml.safe_load(match.group(1)) if yaml else {}
    return block if isinstance(block, dict) else {}


def validate_report(path: Path, *, expect_container_only: bool = False) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"Missing report: {path}"]

    text = path.read_text(encoding="utf-8")
    lower = text.lower()

    for key in REQUIRED_SIGNOFF_KEYS:
        if key not in lower:
            errors.append(f"{path.name}: missing sign-off key {key!r}")

    signoff = _parse_signoff_yaml(text)
    if not signoff:
        errors.append(f"{path.name}: missing fenced ```yaml sign-off block")
        return errors

    physical = signoff.get("physical_validation_performed")
    container_only = signoff.get("container_only")
    env = signoff.get("validation_environment")
    approved = signoff.get("approved_for_beta_hardware_claim")

    if expect_container_only:
        if physical is True:
            errors.append(f"{path.name}: example must not claim physical_validation_performed: true")
        if container_only is not True:
            errors.append(f"{path.name}: example must set container_only: true")
        if env != "container":
            errors.append(f"{path.name}: example must set validation_environment: container")
        if approved is True:
            errors.append(f"{path.name}: example must not approve beta hardware claim")
        if not any(marker in lower for marker in CONTAINER_MARKERS):
            errors.append(f"{path.name}: example must clearly label container-only evidence")
    else:
        if physical is True and env != "physical":
            errors.append(f"{path.name}: physical_validation_performed true requires validation_environment: physical")
        if physical is True and approved is not True:
            errors.append(f"{path.name}: physical validation requires approved_for_beta_hardware_claim review")

    if physical is not True:
        for claim in FORBIDDEN_CLAIMS:
            if claim in lower and "not" not in lower[: lower.find(claim)]:
                # Allow explicit negations in template
                if "do not" in lower or "false" in lower:
                    continue
                errors.append(f"{path.name}: may falsely claim: {claim}")

    if "serial" in lower and "do not" not in lower and "no serial" not in lower:
        if re.search(r"serial\s*[:|]\s*\S+", lower):
            errors.append(f"{path.name}: must not include device serial numbers")

    return errors


def validate_matrix() -> list[str]:
    errors: list[str] = []
    if yaml is None:
        return ["PyYAML required"]
    if not MATRIX.exists():
        return [f"Missing matrix: {MATRIX}"]

    data = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
    areas = data.get("validation_areas", [])
    area_ids = {a["id"] for a in areas if isinstance(a, dict) and "id" in a}
    defaults = data.get("area_defaults", {})
    if not area_ids:
        errors.append("Matrix missing validation_areas")
    if set(defaults.keys()) != area_ids:
        missing = area_ids - set(defaults.keys())
        extra = set(defaults.keys()) - area_ids
        if missing:
            errors.append(f"area_defaults missing: {sorted(missing)}")
        if extra:
            errors.append(f"area_defaults unknown keys: {sorted(extra)}")

    devices = data.get("reference_devices", {})
    if not devices:
        errors.append("Matrix missing reference_devices")

    container = data.get("container_reference", {})
    report = container.get("evidence_report")
    if not report:
        errors.append("container_reference missing evidence_report")
    elif not (ROOT / report).exists():
        errors.append(f"container_reference evidence_report missing file: {report}")

    for device_id, device in devices.items():
        if device.get("validation_status") == "validated" and not device.get("evidence_report"):
            errors.append(f"{device_id}: validated status requires evidence_report path")

    return errors


def validate_template() -> list[str]:
    errors: list[str] = []
    if not TEMPLATE.exists():
        return [f"Missing template: {TEMPLATE}"]
    text = TEMPLATE.read_text(encoding="utf-8").lower()
    if "physical_validation_performed" not in text:
        errors.append("Template missing physical_validation_performed sign-off")
    if "do not claim physical" not in text:
        errors.append("Template must warn against false physical claims")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate hardware validation package.")
    parser.add_argument("report", nargs="?", type=Path, help="Optional report path to validate.")
    args = parser.parse_args()

    errors: list[str] = []
    errors.extend(validate_matrix())
    errors.extend(validate_template())
    errors.extend(validate_report(TEMPLATE))
    errors.extend(validate_report(EXAMPLE, expect_container_only=True))

    if args.report:
        expect_container = "example" in args.report.name.lower()
        errors.extend(validate_report(args.report, expect_container_only=expect_container))

    if errors:
        print("validate_hardware_report FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("validate_hardware_report: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
