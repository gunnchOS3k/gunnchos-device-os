#!/usr/bin/env python3
"""Collect safe host hardware info for reference validation reports.

Collects only non-sensitive, non-identifying host metadata suitable for
validation report attachments. Does NOT collect serial numbers, MAC
addresses, hostnames, usernames, or other private identifiers.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Exact keys that must never appear in output.
FORBIDDEN_KEYS = frozenset(
    {
        "serial",
        "serial_number",
        "mac",
        "mac_address",
        "uuid",
        "hostname",
        "username",
        "imei",
        "meid",
    }
)

# Value patterns indicating private identifiers.
MAC_PATTERN = re.compile(
    r"([0-9a-f]{2}[:-]){5}[0-9a-f]{2}",
    re.IGNORECASE,
)


def _contains_forbidden_key(key: str) -> bool:
    lower = key.lower().replace("-", "_")
    if lower in FORBIDDEN_KEYS:
        return True
    return any(lower.endswith(f"_{token}") or lower.startswith(f"{token}_") for token in FORBIDDEN_KEYS)


def _contains_forbidden_value(text: str) -> bool:
    if MAC_PATTERN.search(text):
        return True
    lower = text.lower()
    if "serial number" in lower or lower.startswith("sn:"):
        return True
    return False


def _round_gb(bytes_value: int | float | None) -> float | None:
    if bytes_value is None:
        return None
    return round(float(bytes_value) / (1024**3), 1)


def _safe_memory_gb() -> float | None:
    try:
        import psutil  # type: ignore

        return _round_gb(psutil.virtual_memory().total)
    except Exception:
        pass
    if sys.platform == "darwin":
        try:
            import subprocess

            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
            return _round_gb(int(out))
        except Exception:
            return None
    if sys.platform == "linux":
        try:
            meminfo = Path("/proc/meminfo").read_text(encoding="utf-8")
            for line in meminfo.splitlines():
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return _round_gb(kb * 1024)
        except Exception:
            return None
    return None


def _safe_disk_gb() -> float | None:
    try:
        usage = shutil.disk_usage("/")
        return _round_gb(usage.total)
    except Exception:
        return None


def _safe_network_interfaces() -> list[dict[str, str]]:
    """Return interface names and link types only — no addresses."""
    interfaces: list[dict[str, str]] = []
    if sys.platform == "linux":
        net = Path("/sys/class/net")
        if net.exists():
            for iface in sorted(net.iterdir()):
                name = iface.name
                if name == "lo" or _contains_forbidden_key(name):
                    continue
                kind = "unknown"
                type_file = iface / "type"
                if type_file.exists():
                    kind = type_file.read_text(encoding="utf-8").strip()
                interfaces.append({"name": name, "type": kind})
    elif sys.platform == "darwin":
        try:
            import subprocess

            out = subprocess.check_output(["networksetup", "-listallhardwareports"], text=True)
            current = ""
            for line in out.splitlines():
                if line.startswith("Hardware Port:"):
                    current = line.split(":", 1)[1].strip()
                elif line.startswith("Device:") and current:
                    dev = line.split(":", 1)[1].strip()
                    if not _contains_forbidden_key(dev):
                        interfaces.append({"name": dev, "type": current})
                    current = ""
        except Exception:
            pass
    return interfaces


def collect_host_info() -> dict[str, Any]:
    """Build a safe host snapshot dict."""
    snapshot: dict[str, Any] = {
        "schema_version": 1,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "collector": "scripts/collect_reference_hardware_info.py",
        "claim_boundary": "Safe host metadata only — not physical SKU validation evidence.",
        "os": platform.system(),
        "os_release": platform.release(),
        "machine": platform.machine(),
        "architecture": platform.machine(),
        "platform": platform.platform(aliased=True),
        "cpu_platform": platform.processor() or platform.machine(),
        "python_version": platform.python_version(),
        "memory_gb_rounded": _safe_memory_gb(),
        "root_disk_gb_rounded": _safe_disk_gb(),
        "network_interfaces": _safe_network_interfaces(),
        "in_container": _detect_container(),
    }
    return snapshot


def _detect_container() -> bool:
    if os.environ.get("container") or os.environ.get("KUBERNETES_SERVICE_HOST"):
        return True
    if Path("/.dockerenv").exists():
        return True
    if Path("/run/.containerenv").exists():
        return True
    return False


def validate_snapshot(snapshot: dict[str, Any]) -> list[str]:
    """Ensure snapshot contains no forbidden identifiers."""
    errors: list[str] = []

    def walk(obj: Any, path: str = "") -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                full = f"{path}.{key}" if path else key
                if _contains_forbidden_key(str(key)):
                    errors.append(f"Forbidden key: {full}")
                walk(value, full)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")
        elif isinstance(obj, str) and _contains_forbidden_value(obj):
            errors.append(f"Forbidden value at {path}: {obj[:40]!r}")

    walk(snapshot)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect safe host hardware info.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON snapshot to this path (default: stdout).",
    )
    parser.add_argument(
        "--validate-only",
        type=Path,
        help="Validate an existing snapshot JSON file.",
    )
    args = parser.parse_args()

    if args.validate_only:
        data = json.loads(args.validate_only.read_text(encoding="utf-8"))
        errors = validate_snapshot(data)
        if errors:
            for e in errors:
                print(f"ERROR: {e}")
            return 1
        print(f"Snapshot OK: {args.validate_only}")
        return 0

    snapshot = collect_host_info()
    errors = validate_snapshot(snapshot)
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1

    payload = json.dumps(snapshot, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(f"Wrote safe host snapshot: {args.output}")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
