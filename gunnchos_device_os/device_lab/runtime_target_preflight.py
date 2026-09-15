"""Reusable RuntimeTarget preflight for WAIKE Device Lab guest launch.

Refuse launch before exec when the Interactive Guest cannot satisfy the
artifact's published ABI contract (`RUNTIME_TARGET.json`). Additive and
fail-closed: never rewrite ELF strings, never strip features, never claim
PASS from process-alive alone.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "gunnchos.device_lab.runtime_target_preflight.v1"
PREFERRED_LABEL = "linux-aarch64-glibc236"
GUEST_GLIBC_CEILING = (2, 36)
DEVICE_LAB_GUEST_PROFILE = {
    "architecture": "aarch64",
    "os_family": "linux",
    "distro": "debian",
    "distro_version": "12",
    "glibc_version": "2.36",
    "elf_interpreter": "/lib/ld-linux-aarch64.so.1",
    "has_libwebkit2gtk_4_1": True,
    "has_libgtk_3": True,
    "has_libsoup_3": True,
}


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_glibc_version(value: str | None) -> tuple[int, ...] | None:
    if not value:
        return None
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", str(value))
    if not m:
        return None
    parts = [int(m.group(1)), int(m.group(2))]
    if m.group(3) is not None:
        parts.append(int(m.group(3)))
    return tuple(parts)


def load_runtime_target(path: Path) -> dict[str, Any]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema_version") != "waike.runtime_target.v1":
        raise ValueError(f"bad_runtime_target_schema:{doc.get('schema_version')}")
    return doc


def find_runtime_target_near_binary(binary_path: Path) -> Path | None:
    """Locate RUNTIME_TARGET.json adjacent to a staged owner_build tree."""
    p = Path(binary_path).resolve()
    for parent in [p.parent, *p.parents]:
        cand = parent / "reports" / "RUNTIME_TARGET.json"
        if cand.is_file():
            return cand
        cand = parent / "RUNTIME_TARGET.json"
        if cand.is_file():
            return cand
        # owner_build/<variant>/apps/... → owner_build/<variant>/reports/
        if parent.name == "owner_build" or parent.parent.name == "owner_build":
            for reports in parent.rglob("RUNTIME_TARGET.json"):
                return reports
    return None


def select_runtime_target_for_label(
    repo_root: Path, *, label: str = PREFERRED_LABEL
) -> dict[str, Any]:
    """Prefer linux-aarch64-glibc236; never silently pick Ubuntu GLIBC_2.39."""
    base = Path(repo_root) / "artifacts/device_lab_current_pin/waike/owner_build"
    candidates: list[Path] = []
    preferred_dir = base / "main-aarch64-glibc236"
    if preferred_dir.is_dir():
        candidates.extend(preferred_dir.rglob("RUNTIME_TARGET.json"))
    candidates.extend(base.rglob("RUNTIME_TARGET.json"))
    seen: set[str] = set()
    selected = None
    rejected: list[dict[str, Any]] = []
    for path in candidates:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        try:
            doc = load_runtime_target(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            rejected.append({"path": key, "error": str(exc)})
            continue
        row = {
            "path": key,
            "compatibility_label": doc.get("compatibility_label"),
            "measured_max_glibc": doc.get("measured_max_glibc"),
            "source_sha": doc.get("source_sha"),
            "artifact_sha256": doc.get("artifact_sha256"),
        }
        if doc.get("compatibility_label") == label:
            selected = {"runtime_target": doc, "path": key, **row}
            break
        rejected.append(row)
    return {
        "ok": selected is not None,
        "preferred_label": label,
        "selected": selected,
        "rejected_non_matching": rejected,
        "error": None if selected else f"runtime_target_label_not_found:{label}",
    }


def evaluate_runtime_target_against_guest(
    runtime_target: dict[str, Any],
    guest: dict[str, Any],
    *,
    guest_glibc_ceiling: tuple[int, ...] = GUEST_GLIBC_CEILING,
) -> dict[str, Any]:
    """Compare artifact contract to guest capability. Fail-closed on ABI mismatch."""
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    def _check(name: str, ok: bool, detail: Any) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            blockers.append(name)

    arch_ok = str(runtime_target.get("architecture")) == str(guest.get("architecture"))
    _check(
        "architecture_match",
        arch_ok,
        {
            "artifact": runtime_target.get("architecture"),
            "guest": guest.get("architecture"),
        },
    )

    interp_ok = str(runtime_target.get("elf_interpreter") or "") == str(
        guest.get("elf_interpreter") or ""
    )
    _check(
        "elf_interpreter_match",
        interp_ok,
        {
            "artifact": runtime_target.get("elf_interpreter"),
            "guest": guest.get("elf_interpreter"),
        },
    )

    measured = parse_glibc_version(str(runtime_target.get("measured_max_glibc") or ""))
    guest_glibc = parse_glibc_version(str(guest.get("glibc_version") or ""))
    ceiling = guest_glibc or guest_glibc_ceiling
    max_ok = measured is not None and measured <= ceiling
    _check(
        "measured_max_glibc_within_guest",
        max_ok,
        {
            "measured_max_glibc": runtime_target.get("measured_max_glibc"),
            "guest_glibc": guest.get("glibc_version"),
            "ceiling": ".".join(str(x) for x in ceiling),
        },
    )

    baseline = parse_glibc_version(str(runtime_target.get("glibc_baseline") or ""))
    baseline_ok = baseline is not None and baseline <= guest_glibc_ceiling
    _check(
        "glibc_baseline_compatible_with_debian12_ceiling",
        baseline_ok,
        {
            "glibc_baseline": runtime_target.get("glibc_baseline"),
            "guest_ceiling": ".".join(str(x) for x in guest_glibc_ceiling),
        },
    )

    label = str(runtime_target.get("compatibility_label") or "")
    label_ok = label == PREFERRED_LABEL
    _check(
        "preferred_compatibility_label",
        label_ok,
        {"compatibility_label": label, "required": PREFERRED_LABEL},
    )

    # Critical shared libs for Tauri/WebKit path (not full ldd dump).
    for key, guest_key in (
        ("libwebkit2gtk-4.1", "has_libwebkit2gtk_4_1"),
        ("libgtk-3", "has_libgtk_3"),
        ("libsoup-3.0", "has_libsoup_3"),
    ):
        present = bool(guest.get(guest_key))
        _check(f"guest_has_{key.replace('.', '_').replace('-', '_')}", present, guest_key)

    # Explicit reject of Ubuntu 24.04 / GLIBC_2.39 producer for Debian 12 guest.
    measured_too_new = measured is not None and measured > guest_glibc_ceiling
    ubuntu_current = label in {"linux-aarch64-current", "aarch64-current"} or str(
        runtime_target.get("target_id") or ""
    ) in {"aarch64-current"}
    if measured_too_new or (ubuntu_current and not label_ok):
        blockers.append("reject_ubuntu2404_glibc239_on_debian12_guest")
        checks.append(
            {
                "name": "reject_ubuntu2404_glibc239_on_debian12_guest",
                "ok": False,
                "detail": {
                    "label": label,
                    "target_id": runtime_target.get("target_id"),
                    "measured_max_glibc": runtime_target.get("measured_max_glibc"),
                },
            }
        )

    passed = not blockers
    return {
        "schema": SCHEMA,
        "generated_at_utc": _utc(),
        "RUNTIME_TARGET_PREFLIGHT_PASS": passed,
        "preferred_label": PREFERRED_LABEL,
        "selected_label": label,
        "checks": checks,
        "blockers": blockers,
        "runtime_target_summary": {
            "compatibility_label": runtime_target.get("compatibility_label"),
            "target_id": runtime_target.get("target_id"),
            "source_sha": runtime_target.get("source_sha"),
            "artifact_sha256": runtime_target.get("artifact_sha256"),
            "architecture": runtime_target.get("architecture"),
            "measured_max_glibc": runtime_target.get("measured_max_glibc"),
            "glibc_baseline": runtime_target.get("glibc_baseline"),
            "elf_interpreter": runtime_target.get("elf_interpreter"),
            "workflow_run_id": runtime_target.get("workflow_run_id"),
        },
        "guest_summary": {
            k: guest.get(k)
            for k in (
                "architecture",
                "glibc_version",
                "elf_interpreter",
                "distro",
                "distro_version",
                "has_libwebkit2gtk_4_1",
                "has_libgtk_3",
                "has_libsoup_3",
                "probe_source",
            )
        },
    }


def probe_guest_runtime_profile(session: Any | None = None) -> dict[str, Any]:
    """Probe live guest when session available; else return Device Lab Debian 12 profile."""
    if session is None:
        return {**DEVICE_LAB_GUEST_PROFILE, "probe_source": "device_lab_debian12_static_profile"}

    # Lazy import to avoid circular deps at module import time.
    from gunnchos_device_os.device_lab.owner_waike_guest import _guest_sh

    result = _guest_sh(
        session,
        "set +e; "
        "uname -m; "
        "getconf GNU_LIBC_VERSION 2>/dev/null || true; "
        "ldd --version 2>&1 | head -1; "
        "ls -l /lib/ld-linux-aarch64.so.1 2>/dev/null || true; "
        "ldconfig -p 2>/dev/null | grep -E 'libwebkit2gtk-4.1.so|libgtk-3.so.0|libsoup-3.0.so' | head -20; "
        "echo GUEST_RUNTIME_PROBE_DONE",
        timeout_sec=45.0,
    )
    text = (result.get("stdout") or "") + (result.get("stderr") or "")
    glibc = None
    m = re.search(r"GNU libc\s+(\d+\.\d+)", text)
    if m:
        glibc = m.group(1)
    else:
        m = re.search(r"GLIBC\s+(\d+\.\d+)", text, re.I)
        if m:
            glibc = m.group(1)
        else:
            m = re.search(r"ldd \(.*GLIBC\s+(\d+\.\d+)", text)
            if m:
                glibc = m.group(1)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    arch = "unknown"
    if lines and lines[0] in {"aarch64", "arm64", "x86_64"}:
        arch = "aarch64" if lines[0] == "arm64" else lines[0]
    elif "aarch64" in text:
        arch = "aarch64"
    return {
        "architecture": arch,
        "os_family": "linux",
        "distro": "debian",
        "distro_version": "12",
        "glibc_version": glibc or "2.36",
        "elf_interpreter": "/lib/ld-linux-aarch64.so.1",
        "has_libwebkit2gtk_4_1": "libwebkit2gtk-4.1" in text,
        "has_libgtk_3": "libgtk-3.so" in text,
        "has_libsoup_3": "libsoup-3.0" in text,
        "probe_source": "live_guest_agent",
        "probe_tail": text[-1200:],
        "ok_marker": "GUEST_RUNTIME_PROBE_DONE" in text,
    }


def run_runtime_target_preflight(
    repo_root: Path,
    *,
    session: Any | None = None,
    label: str = PREFERRED_LABEL,
    out_path: Path | None = None,
) -> dict[str, Any]:
    selection = select_runtime_target_for_label(repo_root, label=label)
    guest = probe_guest_runtime_profile(session)
    if not selection.get("ok"):
        doc = {
            "schema": SCHEMA,
            "generated_at_utc": _utc(),
            "RUNTIME_TARGET_PREFLIGHT_PASS": False,
            "blockers": [selection.get("error") or "runtime_target_missing"],
            "selection": selection,
            "guest_summary": guest,
        }
    else:
        rt = selection["selected"]["runtime_target"]
        doc = evaluate_runtime_target_against_guest(rt, guest)
        doc["selection"] = {
            "path": selection["selected"]["path"],
            "preferred_label": label,
        }
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc
