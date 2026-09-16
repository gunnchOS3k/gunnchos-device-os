"""Stage authentic WAIKE Learning OS owner artifacts for Interactive Guest.

System of record is the Platform Tauri client from accepted-main
`gunnchos-waike-learning-platform` — never Device OS seed HTML, research-ops
alone, curriculum-only packs, or the protocol fixture at
fixtures/learning_os/waike-learning-os.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ACCEPTED_WAIKE_LP_SHA = "232fc8dc3aa10d3dd644ef48d1d8c63da50d4d3c"
ACCEPTED_WAIKE_OPS_SHA = "fbf7685bc5686201ccaa0128ee83346d59b3d584"
# Updated when ACCEPTED_MAIN_PIN_MANIFEST is recomputed for WAIKE #12 hub policy pin.
PIN_MANIFEST_SHA256 = "47fe0c86856c4eec795a7b28c582532d612175475a83f91ad315720326a5ce15"
BUNDLE_ID = "com.gunnchos.waike.learning"
APP_VERSION = "0.1.0"

# Gate D linux CI artifact retained for x86_64 targets (pre-#12 binary still staged).
GATE_D_LINUX_ARTIFACT_ID = "10041457013"
GATE_D_LINUX_SHA256 = (
    "8689a422404800ef6ef6442864e08228c69ccb0e705b15f8e1d1d94eee98bdef"
)

# Accepted-main Debian 12 / glibc236 aarch64 Device Lab artifact (merge #12 / run 35046618011).
# Prefer this over Ubuntu 24.04 aarch64-current (GLIBC_2.39) for Interactive Guest.
MAIN_AARCH64_GLIBC236_ARTIFACT_ID = "10426884231"
MAIN_AARCH64_GLIBC236_WORKFLOW_RUN_ID = "35046618011"
MAIN_AARCH64_GLIBC236_SHA256 = (
    "3df1e42e5d6c1b8b7e8ee31a636b2a6bec49120f38b6d28bd290b8a6e3fa1207"
)
MAIN_AARCH64_GLIBC236_LABEL = "linux-aarch64-glibc236"

# Retained Ubuntu 24.04 ARM producer (aarch64-current) — NOT for Debian 12 guest exec.
MAIN_AARCH64_ARTIFACT_ID = "10415274147"
MAIN_AARCH64_WORKFLOW_RUN_ID = "35015695037"
MAIN_AARCH64_SHA256 = (
    "1725b2122c36ee8c008fc583569470496082763b6491a01be1b3b43a2d371c8b"
)
MAIN_AARCH64_ARTIFACT_SOURCE_SHA = ACCEPTED_WAIKE_LP_SHA

DEVICE_LAB_HUB_ENDPOINT_POLICY_V1 = {
    "schema_version": "hub_endpoint_policy.v1",
    "authorized_hub_base_url": "http://10.0.2.2:8787",
    "deployment_id": "device-lab-qemu-guest",
    "site_id": "device-lab",
    "require_https": False,
    "allow_insecure_local": True,
    "provenance": "device_lab_fixture",
    "expires_at": None,
}


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def _repos_root(repo_root: Path) -> Path:
    """Device OS may live in repos/gunnchos-device-os or .../.worktrees/<name>."""
    p = Path(repo_root).resolve()
    # .worktrees/<branch> → device-os → repos
    if p.parent.name == ".worktrees":
        return p.parent.parent.parent
    # repos/gunnchos-device-os
    if p.name == "gunnchos-device-os":
        return p.parent
    return p.parent


def resolve_waike_lp_checkout(repo_root: Path) -> Path:
    env = os.environ.get("WAIKE_LP_ROOT")
    if env:
        return Path(env).resolve()
    repos = _repos_root(repo_root)
    candidates = [
        Path(repo_root) / ".deps" / "current-pin-waike-lp",
        repos / "gunnchos-waike-learning-platform",
    ]
    for c in candidates:
        if (c / "apps" / "client").is_dir():
            return c.resolve()
    raise FileNotFoundError("waike_learning_platform_checkout_missing")


def resolve_waike_ops_checkout(repo_root: Path) -> Path:
    env = os.environ.get("WAIKE_ROOT")
    if env:
        return Path(env).resolve()
    repos = _repos_root(repo_root)
    candidates = [
        repos / "waike-research-ops",
        Path(repo_root) / ".deps" / "waike-research-ops",
    ]
    for path in candidates:
        if path.is_dir():
            return path.resolve()
    raise FileNotFoundError("waike_research_ops_checkout_missing")



def verify_pin_checkouts(repo_root: Path) -> dict[str, Any]:
    lp = resolve_waike_lp_checkout(repo_root)
    ops = resolve_waike_ops_checkout(repo_root)
    lp_sha = _git(lp, "rev-parse", "HEAD")
    # Detached accepted-main pin preferred; also accept origin/main match.
    try:
        lp_origin = subprocess.check_output(
            ["git", "-C", str(lp), "rev-parse", "origin/main"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        lp_origin = None
    # Prefer origin/main when present; detached pin HEADs are valid.
    try:
        ops_sha = _git(ops, "rev-parse", "HEAD")
    except subprocess.CalledProcessError as exc:
        return {"ok": False, "error": f"ops_rev_parse:{exc}"}
    try:
        ops_origin = subprocess.check_output(
            ["git", "-C", str(ops), "rev-parse", "origin/main"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        ops_origin = ops_sha
    dirty_lp = bool(_git(lp, "status", "--porcelain"))
    dirty_ops = bool(_git(ops, "status", "--porcelain"))
    lp_ok = lp_sha == ACCEPTED_WAIKE_LP_SHA or lp_origin == ACCEPTED_WAIKE_LP_SHA
    ops_ok = ops_origin == ACCEPTED_WAIKE_OPS_SHA or ops_sha == ACCEPTED_WAIKE_OPS_SHA
    return {
        "ok": bool(lp_ok and ops_ok and not dirty_lp),
        "learning_platform": {
            "path": str(lp),
            "head": lp_sha,
            "origin_main": lp_origin,
            "expected": ACCEPTED_WAIKE_LP_SHA,
            "match": lp_ok,
            "dirty": dirty_lp,
        },
        "research_ops": {
            "path": str(ops),
            "head": ops_sha,
            "origin_main": ops_origin,
            "expected": ACCEPTED_WAIKE_OPS_SHA,
            "match": ops_ok,
            "dirty": dirty_ops,
        },
        "note": (
            "Dirty research-ops allowed only if origin/main pin matches; "
            "learning-platform must be clean accepted-main for PASS evidence."
        ),
    }


def _probe_binary(path: Path) -> dict[str, Any]:
    digest = _sha256_file(path)
    try:
        probe = subprocess.check_output(["file", "-b", str(path)], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        probe = "unknown"
    arch = "unknown"
    if "x86-64" in probe or "x86_64" in probe:
        arch = "x86_64"
    elif "ARM aarch64" in probe or "arm64" in probe:
        arch = "aarch64"
    return {
        "path": str(path),
        "sha256": digest,
        "size_bytes": path.stat().st_size,
        "file_probe": probe,
        "arch": arch,
        "fixture_rejected": "fixtures/learning_os" not in str(path),
    }


def locate_staged_linux_binary(repo_root: Path) -> dict[str, Any]:
    """Prefer accepted-main glibc236 aarch64; retain Ubuntu ARM + x86_64 Gate D."""
    base = repo_root / "artifacts/device_lab_current_pin/waike/owner_build"
    ordered: list[Path] = []
    ordered.extend(base.glob("main-aarch64-glibc236/**/waike-learning-client"))
    ordered.extend(base.glob("main-aarch64-linux/**/waike-learning-client"))
    ordered.extend(base.glob("gate-d-linux/**/waike-learning-client"))
    ordered.extend(base.glob("**/waike-learning-client"))
    seen: set[str] = set()
    found: list[dict[str, Any]] = []
    for c in ordered:
        if not c.is_file():
            continue
        key = str(c.resolve())
        if key in seen:
            continue
        seen.add(key)
        found.append(_probe_binary(c))
    # Prefer exact glibc236 hash, never silently pick Ubuntu GLIBC_2.39 for guest.
    preferred = None
    for row in found:
        if row["sha256"] == MAIN_AARCH64_GLIBC236_SHA256 and row["arch"] == "aarch64":
            preferred = row
            break
    if preferred is None:
        # Do not auto-select Ubuntu 24.04 aarch64-current for Device Lab guest.
        for row in found:
            if row["arch"] == "x86_64":
                preferred = row
                break
    if preferred is None and found:
        preferred = found[0]
    if preferred is None:
        return {"ok": False, "error": "linux_binary_not_staged", "searched": str(base)}
    arch = preferred["arch"]
    is_glibc236 = preferred["sha256"] == MAIN_AARCH64_GLIBC236_SHA256
    is_ubuntu_arm = preferred["sha256"] == MAIN_AARCH64_SHA256
    if is_glibc236:
        artifact_id = MAIN_AARCH64_GLIBC236_ARTIFACT_ID
        workflow_run_id = MAIN_AARCH64_GLIBC236_WORKFLOW_RUN_ID
        label = MAIN_AARCH64_GLIBC236_LABEL
    elif arch == "aarch64":
        artifact_id = MAIN_AARCH64_ARTIFACT_ID
        workflow_run_id = MAIN_AARCH64_WORKFLOW_RUN_ID
        label = "linux-aarch64-current"
    else:
        artifact_id = GATE_D_LINUX_ARTIFACT_ID
        workflow_run_id = None
        label = "linux-x86_64-gate-d"
    return {
        "ok": True,
        **preferred,
        "matches_gate_d_linux_sha256": preferred["sha256"] == GATE_D_LINUX_SHA256,
        "matches_main_aarch64_sha256": is_ubuntu_arm,
        "matches_main_aarch64_glibc236_sha256": is_glibc236,
        "compatibility_label": label,
        "artifact_id": artifact_id,
        "workflow_run_id": workflow_run_id,
        "artifact_source_sha": (
            ACCEPTED_WAIKE_LP_SHA if (is_glibc236 or is_ubuntu_arm or arch == "x86_64") else None
        ),
        "x86_64_retained": any(r["arch"] == "x86_64" for r in found),
        "ubuntu_arm_retained_not_for_debian12": any(
            r["sha256"] == MAIN_AARCH64_SHA256 for r in found
        ),
        "staged_variants": [
            {"arch": r["arch"], "sha256": r["sha256"], "path": r["path"]} for r in found
        ],
    }


def write_runtime_provenance(repo_root: Path, out_dir: Path) -> dict[str, Any]:
    pins = verify_pin_checkouts(repo_root)
    binary = locate_staged_linux_binary(repo_root)
    doc = {
        "schema": "gunnchos.device_lab.waike_runtime_provenance.v1",
        "generated_at_utc": _utc(),
        "pin_manifest_sha256": PIN_MANIFEST_SHA256,
        "system_of_record": "platform_tauri_learning_os",
        "bundle_id": BUNDLE_ID,
        "app_version": APP_VERSION,
        "accepted_main": {
            "repository": "gunnchOS3k/gunnchos-waike-learning-platform",
            "sha": ACCEPTED_WAIKE_LP_SHA,
            "curriculum_ops_sha": ACCEPTED_WAIKE_OPS_SHA,
        },
        "rejected_surrogates": [
            "apps/waike_learning/index.html seed companion",
            "fixtures/learning_os/waike-learning-os protocol stub",
            "product_use waike_guest_pack static HTML collector",
            "research-ops curriculum alone",
            "screenshots / API-only / process-alive alone",
        ],
        "pin_verification": pins,
        "authentic_linux_ci_artifact": binary,
        "guest_arch_expectation": "aarch64",
        "ci_linux_artifact_arch": binary.get("arch"),
        "arch_gap": binary.get("arch") == "x86_64",
        "compatibility_label": binary.get("compatibility_label"),
        "matches_main_aarch64_glibc236_sha256": binary.get(
            "matches_main_aarch64_glibc236_sha256"
        ),
        "compatibility_plan": (
            "Device OS Interactive Guest is Debian 12 / glibc 2.36 aarch64. "
            "Prefer accepted-main linux-aarch64-glibc236 artifact; retain "
            "Ubuntu aarch64-current and x86_64 Gate D but never exec Ubuntu "
            "GLIBC_2.39 ELF on Debian 12 guest. RuntimeTarget preflight must "
            "PASS before journey."
        ),
        "launcher_contract": "gunnchos_device_os.learning_os_launcher + NativeLaunchAdapter",
        "claim_boundary": (
            "SoR is Platform Tauri Learning OS. Device OS is thin launcher / "
            "package lifecycle / permissions / continuity only."
        ),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "WAIKE_RUNTIME_PROVENANCE.json"
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def stage_owner_waike_bundle(repo_root: Path, staging: Path) -> dict[str, Any]:
    """Prepare HTTP-served bundle: binary + install layout + provenance."""
    staging.mkdir(parents=True, exist_ok=True)
    provenance = write_runtime_provenance(repo_root, staging)
    binary = locate_staged_linux_binary(repo_root)
    if not binary.get("ok"):
        return {
            "ok": False,
            "error": binary.get("error"),
            "provenance": provenance,
        }
    src = Path(binary["path"])
    bin_dir = staging / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    dest = bin_dir / "waike-learning-os"
    shutil.copy2(src, dest)
    dest.chmod(dest.stat().st_mode | 0o111)
    (bin_dir / "VERSION").write_text(APP_VERSION + "\n", encoding="utf-8")
    meta = {
        "bundle_id": BUNDLE_ID,
        "version": APP_VERSION,
        "artifact_sha256": _sha256_file(dest),
        "source_sha256": binary["sha256"],
        "source_arch": binary["arch"],
        "platform_sha": ACCEPTED_WAIKE_LP_SHA,
        "curriculum_ops_sha": ACCEPTED_WAIKE_OPS_SHA,
        "gate_d_artifact_id": GATE_D_LINUX_ARTIFACT_ID,
        "main_aarch64_artifact_id": binary.get("artifact_id"),
        "workflow_run_id": binary.get("workflow_run_id"),
        "artifact_source_sha": binary.get("artifact_source_sha"),
        "compatibility_label": binary.get("compatibility_label"),
        "matches_main_aarch64_glibc236_sha256": binary.get(
            "matches_main_aarch64_glibc236_sha256"
        ),
        "x86_64_retained": binary.get("x86_64_retained"),
        "ubuntu_arm_retained_not_for_debian12": binary.get(
            "ubuntu_arm_retained_not_for_debian12"
        ),
        "fixture": False,
        "system_of_record": "platform_tauri_learning_os",
    }
    (bin_dir / "INSTALLED.json").write_text(json.dumps(meta, indent=2) + "\n")
    # Ship Device OS learning-os launcher modules for in-guest NativeLaunchAdapter.
    # Additive: guest previously only had /opt/gunnchos/lib when image-baked.
    device_os_lib_root = staging / "device_os_lib"
    if device_os_lib_root.exists():
        shutil.rmtree(device_os_lib_root)
    src_pkg = Path(repo_root) / "gunnchos_device_os"

    def _ignore_heavy(_dir: str, names: list[str]) -> set[str]:
        drop = {
            "__pycache__",
            ".pytest_cache",
            "device_lab",
            "os_build",
            "cont_viii",
            "cont_ix",
            "wave009_os020",
            "a_pkt003",
            "product_use",
            "service_continuity_execution",
            "cloud_dev_plane",
            "cloud_edge",
            "connectivity",
            "boot",
            "bootable_image",
        }
        return {n for n in names if n in drop or n.endswith(".pyc")}

    shutil.copytree(src_pkg, device_os_lib_root / "gunnchos_device_os", ignore=_ignore_heavy)
    # Stage accepted TEST_ONLY verify key (same fixture Windows Pilot 0 uses).
    try:
        lp_root = resolve_waike_lp_checkout(repo_root)
        key_src = lp_root / "contracts/fixtures/keys/TEST_ONLY_ed25519_public.key"
    except FileNotFoundError:
        key_src = Path()
    if key_src.is_file():
        keys_dir = staging / "contracts" / "fixtures" / "keys"
        keys_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(key_src, keys_dir / "TEST_ONLY_ed25519_public.key")
        xdg = staging / "xdg" / "waike-learning-os"
        xdg.mkdir(parents=True, exist_ok=True)
        shutil.copy2(key_src, xdg / "TEST_ONLY_ed25519_public.key")
    # HubEndpointPolicy v1 Device Lab fixture (authorizes http://10.0.2.2:8787 only).
    policy_dir = staging / "contracts" / "fixtures"
    policy_dir.mkdir(parents=True, exist_ok=True)
    (policy_dir / "device_lab_hub_endpoint_policy.v1.json").write_text(
        json.dumps(DEVICE_LAB_HUB_ENDPOINT_POLICY_V1, indent=2) + "\n", encoding="utf-8"
    )
    policy_xdg = staging / "xdg" / "com.gunnchos.waike.learning"
    policy_xdg.mkdir(parents=True, exist_ok=True)
    (policy_xdg / "hub_endpoint_policy.v1.json").write_text(
        json.dumps(DEVICE_LAB_HUB_ENDPOINT_POLICY_V1, indent=2) + "\n", encoding="utf-8"
    )
    # Wrapper used when guest needs qemu-user for x86_64 ELF on aarch64.
    wrapper = staging / "bin" / "waike-learning-os.qemu-x86_64-wrapper.sh"
    wrapper.write_text(
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "REAL=\"$(dirname \"$0\")/waike-learning-os.real\"\n"
        "if [ -x /usr/bin/qemu-x86_64-static ]; then\n"
        "  exec /usr/bin/qemu-x86_64-static \"$REAL\" \"$@\"\n"
        "elif [ -x /usr/bin/qemu-x86_64 ]; then\n"
        "  exec /usr/bin/qemu-x86_64 \"$REAL\" \"$@\"\n"
        "else\n"
        "  exec \"$REAL\" \"$@\"\n"
        "fi\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    manifest = {
        "schema": "gunnchos.device_lab.owner_waike_bundle.v1",
        "generated_at_utc": _utc(),
        "ok": True,
        "bundle_id": BUNDLE_ID,
        "install_layout": "bin/waike-learning-os",
        "binary": meta,
        "provenance_path": "WAIKE_RUNTIME_PROVENANCE.json",
        "arch_gap": provenance.get("arch_gap"),
        "pin_ok": bool((provenance.get("pin_verification") or {}).get("ok")),
    }
    (staging / "OWNER_WAIKE_BUNDLE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
