"""Generate / verify Device Lab profiles from accepted hardware truth.

Does not invent MPNs. SILICON_EXACT_EMULATION stays false.
VF4/VF5/VF6 remain PHYSICAL_PENDING in profile honesty fields.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.hardware_truth import load_accepted_hardware_truth
from gunnchos_device_os.device_lab.profiles import CATALOG, PROFILES_DIR, load_profile

DRIFT_KEYS = (
    "ram",
    "storage",
    "compute",
    "exact_mpns",
    "hardware_truth_pin",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _canonical(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False, ensure_ascii=False) + "\n"


def _base_honesty(profile_id: str) -> dict[str, Any]:
    return {
        "schema": "gunnchos.device_lab.device_profile.v1",
        "profile_version": "0.2.0",
        "profile_id": profile_id,
        "SILICON_EXACT_EMULATION": False,
        "BEHAVIORAL_DEVICE_PROFILE": True,
        "VF0_PHYSICAL_TWIN": "PARTIAL",
        "VF4": "PHYSICAL_PENDING",
        "VF5": "PHYSICAL_PENDING",
        "VF6": "PHYSICAL_PENDING",
        "power_model": {
            "status": "TARGET_TBD",
            "measurement_class": "MODELED_TARGET_RANGE",
        },
        "thermal_model": {
            "status": "TARGET_TBD",
            "measurement_class": "MODELED_TARGET_RANGE",
        },
        "performance_model": {
            "status": "FOUNDATION_ONLY",
            "HOST_OBSERVED": "available_at_run",
            "VIRTUAL_CONSTRAINED": "available_when_vm",
            "MODELED_TARGET_RANGE": "schema_present",
            "CALIBRATED_TARGET": "unavailable_pre_EVT",
            "PHYSICAL_MEASURED": "unavailable_pre_EVT",
        },
    }


def _apply_compute_product(out: dict[str, Any], product: dict[str, Any]) -> None:
    compute = product.get("compute") or {}
    out["product"] = product.get("product") or out.get("product")
    out["compute"] = {
        "role": compute.get("role"),
        "vendor": compute.get("vendor"),
        "mpn": compute.get("mpn"),
        "notes": compute.get("notes"),
        "source": compute.get("source"),
        "status": "DESIGN_FREEZE_MPN",
        "measurement_class": "MODELED_TARGET_RANGE",
    }
    out["exact_mpns"] = {"compute": compute.get("mpn")}
    radios = product.get("radios") or {}
    for key in ("wifi_mpn", "wwan_mpn", "tpm_mpn"):
        if radios.get(key):
            out["exact_mpns"][key.replace("_mpn", "")] = radios[key]
    periph = product.get("peripherals") or {}
    for key, val in periph.items():
        if key.endswith("_mpn") and val:
            out["exact_mpns"][key.replace("_mpn", "")] = val
    if product.get("retimer"):
        out["exact_mpns"]["retimer"] = product["retimer"].get("mpn")
        out["retimer"] = product["retimer"]
    ram = product.get("ram") or {}
    out["ram"] = dict(ram)
    storage = product.get("storage") or {}
    out["storage"] = dict(storage)
    if product.get("architecture_guest"):
        out["architecture"] = product["architecture_guest"]


def generate_profile(profile_id: str, *, truth: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a Lab profile document from accepted hardware truth + Lab geometry contracts."""
    truth = truth or load_accepted_hardware_truth()
    pin = truth.get("hardware_repo") or {}
    out = _base_honesty(profile_id)
    out["hardware_truth_pin"] = {
        "hardware_repo_sha": pin.get("pinned_sha"),
        "truth_schema": truth.get("schema"),
        "sources": [s.get("id") for s in (truth.get("sources") or [])],
    }
    out["accepted_source_revisions"] = {
        "hardware_industrial_design_sha": pin.get("pinned_sha"),
        "exact_mpn_matrix": "docs/full_product_family/EXACT_MPN_MATRIX.md",
        "note": "SHAs recorded at sync; do not invent hardware specs",
    }

    products = truth.get("products") or {}

    if profile_id == "student_14_5":
        p = products["student_14_5"]
        _apply_compute_product(out, p)
        disp = p.get("display") or {}
        out["display_outputs"] = [
            {
                "id": "internal-14.5",
                "role": "primary",
                "resolution": disp.get("resolution", "1920x1200"),
                "size_inches": disp.get("size_inches", 14.5),
            }
        ]
        out["display_geometry"] = {
            "size_inches": disp.get("size_inches", 14.5),
            "resolution": disp.get("resolution", "1920x1200"),
            "ppi": 157,
        }
        out["touch"] = True
        out["input_capabilities"] = {"keyboard": True, "touch": True, "stylus": True}
        out["audio_capabilities"] = {"speakers": True, "mic": True}
        out["network_capabilities"] = {
            "wifi": "wifi_7_target_BE200",
            "ethernet_dock_optional": True,
            "offline_capable": True,
        }
        out["cellular_target"] = {"status": "WWAN_OPTIONAL", "mpn": "RM520N-GL"}
        out["dock_capabilities"] = {"supported": True}
        out["ring_capabilities"] = {"supported": False}
        out["AI_capabilities"] = {"local_tutor": True, "cloud_default": False, "tier": "local"}
        out["fidelity_level"] = "VF1"
        out["status_notes"] = [
            "RAM/storage/MPN synced from accepted EXACT_MPN_MATRIX + student BOM",
            "SILICON_EXACT_EMULATION=false; VF4/5/6 PHYSICAL_PENDING",
        ]
        return out

    if profile_id == "dsxl_coder":
        p = products["dsxl_coder"]
        _apply_compute_product(out, p)
        out["display_outputs"] = [
            {"id": "dsxl_top", "role": "primary", "resolution": "1280x720", "size_inches": 7.0},
            {"id": "dsxl_bottom", "role": "secondary", "resolution": "1280x720", "size_inches": 7.0},
        ]
        out["display_geometry"] = {
            "dual_screen": True,
            "per_panel_resolution": "1280x720",
            "size_inches_each": 7.0,
            "note": "Two compositor outputs REQUIRED; one-output instance MUST FAIL D6",
        }
        out["touch"] = True
        out["input_capabilities"] = {"keyboard": True, "touch": True, "controller": False}
        out["audio_capabilities"] = {"speakers": True, "mic": True}
        out["network_capabilities"] = {
            "wifi": "wifi_7_target_BE200",
            "ethernet_dock_optional": True,
            "offline_capable": True,
        }
        out["cellular_target"] = {"status": "none"}
        out["dock_capabilities"] = {"supported": True, "deploy_source": True}
        out["ring_capabilities"] = {"supported": False}
        out["AI_capabilities"] = {"local_code_assist": True, "tier": "local_plus"}
        out["fidelity_level"] = "VF2"
        out["status_notes"] = [
            "Shared COM-HPC-mMTL-155H-32G with Student; dual-eDP carrier differentiator",
            "Storage min 256GB from DEVICE_COMPARISON_MATRIX — SSD MPN not frozen in BOM",
        ]
        return out

    if profile_id == "handheld_hybrid":
        p = products["handheld_hybrid"]
        _apply_compute_product(out, p)
        disp = p.get("display") or {}
        out["display_outputs"] = [
            {
                "id": "internal-8.4",
                "role": "primary",
                "resolution": disp.get("resolution", "1920x1200"),
                "size_inches": disp.get("size_inches", 8.4),
            }
        ]
        out["display_geometry"] = {
            "size_inches": disp.get("size_inches", 8.4),
            "resolution": disp.get("resolution", "1920x1200"),
        }
        out["touch"] = True
        out["input_capabilities"] = {"keyboard": "dock_optional", "touch": True, "controller": True}
        out["audio_capabilities"] = {"speakers": True, "haptic": True, "mic": True}
        out["network_capabilities"] = {
            "wifi": "wifi_6e",
            "ethernet_dock_optional": True,
            "cellular": "simulated_generic",
            "ntn": "simulated",
        }
        out["cellular_target"] = {"status": "simulated_generic"}
        out["dock_capabilities"] = {"supported": True, "usb_c_dp_alt_mode": True}
        out["ring_capabilities"] = {"supported": False}
        out["AI_capabilities"] = {"local": True, "tier": "local"}
        out["fidelity_level"] = "VF1"
        out["status_notes"] = [
            "RM121-D8E32: 8GB LPDDR4X + 32GB eMMC — do not invent NVMe",
            "Undocked handheld baseline; use handheld_docked for office dock",
        ]
        return out

    if profile_id == "dock":
        p = products["dock"]
        _apply_compute_product(out, p)
        out["display_outputs"] = [
            {
                "id": "dock_external",
                "role": "external",
                "resolution": "TARGET_TBD",
                "status": "TARGET_TBD",
                "note": "Appears on dock_attach; disappears on dock_detach",
            }
        ]
        out["display_geometry"] = {"status": "external_via_dock"}
        out["touch"] = False
        out["input_capabilities"] = {"keyboard": "dock_desktop", "mouse": "dock"}
        out["audio_capabilities"] = {"dock_audio": True}
        out["network_capabilities"] = {"ethernet_via_dock": True, "ethernet_mpn": "RTL8156"}
        out["cellular_target"] = {"status": "N/A"}
        out["dock_capabilities"] = {
            "supported": True,
            "adr": "ADR-005-Dock / ADR-HW-002 USB4/TB4",
            "controller_mpn": "JHL8440",
            "retimer_mpn": "JHL9040R",
            "bandwidth_gbps": 40,
            "tb5_claimed": False,
            "virtual_peripherals": [
                "external_display",
                "ethernet",
                "audio",
                "hid",
                "cups_pdf",
                "power_passthrough",
            ],
            "boolean_docked_flag_insufficient": True,
        }
        out["ring_capabilities"] = {"supported": False}
        out["AI_capabilities"] = {"status": "N/A"}
        out["fidelity_level"] = "VF2"
        out["status_notes"] = [
            "Dock controller JHL8440 + retimer JHL9040R from EXACT_MPN_MATRIX",
            "Not a full compute guest; peripheral lifecycle only",
        ]
        return out

    if profile_id == "handheld_docked":
        hand = generate_profile("handheld_hybrid", truth=truth)
        dock = generate_profile("dock", truth=truth)
        out = copy.deepcopy(hand)
        out["profile_id"] = "handheld_docked"
        out["product"] = "Handheld Hybrid + Dock"
        out["display_outputs"] = [
            hand["display_outputs"][0] | {"role": "internal"},
            dock["display_outputs"][0],
        ]
        out["display_geometry"] = {
            "internal": hand["display_geometry"].get("resolution"),
            "external": "TARGET_TBD",
        }
        out["input_capabilities"] = {
            "keyboard": "dock_desktop",
            "touch": True,
            "mouse": "dock",
            "controller": True,
        }
        out["audio_capabilities"] = {"speakers": True, "dock_audio": True, "mic": True}
        out["network_capabilities"] = {
            "wifi": "wifi_6e",
            "ethernet_via_dock": True,
            "offline_capable": True,
            "ethernet_mpn": "RTL8156",
        }
        out["dock_capabilities"] = dock["dock_capabilities"]
        out["exact_mpns"] = {
            **(hand.get("exact_mpns") or {}),
            **(dock.get("exact_mpns") or {}),
        }
        out["compute"] = hand["compute"]
        out["ram"] = hand["ram"]
        out["storage"] = hand["storage"]
        out["fidelity_level"] = "VF2"
        out["status_notes"] = [
            "Composite of handheld_hybrid + dock accepted MPNs",
            "G04 LAB-SCENARIO-OFFICE-DOCK primary profile",
        ]
        return out

    if profile_id == "edge_io_rings":
        p = products["edge_io_rings"]
        _apply_compute_product(out, p)
        out["display_outputs"] = [
            {
                "id": "none",
                "role": "peripheral",
                "note": "Rings are input peripherals; attach to host profile displays",
            }
        ]
        out["display_geometry"] = {"status": "N/A"}
        out["touch"] = False
        out["input_capabilities"] = {"ring_pose": True, "gesture": True, "confidence": True}
        out["audio_capabilities"] = {"status": "N/A"}
        out["network_capabilities"] = {
            "authenticated_transport": True,
            "ble_or_usb": "TARGET_TBD",
        }
        out["cellular_target"] = {"status": "N/A"}
        out["dock_capabilities"] = {"supported": False}
        out["ring_capabilities"] = {
            "supported": True,
            "adr": "ADR-009-Ring-Spatial",
            "mcu_mpn": "nRF52840-QIAA-R",
            "pipeline": [
                "edge_io_sim",
                "authenticated_packet",
                "ring_service",
                "SpatialInputService",
                "input_router",
                "apps",
            ],
            "direct_file_write_not_valid_d6": True,
        }
        out["AI_capabilities"] = {"status": "N/A"}
        out["fidelity_level"] = "VF2"
        out["status_notes"] = [
            "MCU nRF52840-QIAA-R from EXACT_MPN_MATRIX",
            "Spatial accuracy SIMULATED; physical SI PENDING",
        ]
        return out

    if profile_id == "full_ecosystem":
        members = ["student_14_5", "dsxl_coder", "handheld_hybrid", "dock", "edge_io_rings"]
        generated = {m: generate_profile(m, truth=truth) for m in members}
        out["product"] = "Full Ecosystem (Student + DS-XL + Handheld + Dock + Rings + gunnchAI)"
        out["architecture"] = "multi_device_aggregate"
        out["compute_target"] = {
            "status": "FOUNDATION_ARCHITECTURE",
            "note": "Aggregate; smoke only — not simultaneous physical claim",
        }
        out["ram"] = {
            "status": "aggregate",
            "members_gb": {
                "student_14_5": generated["student_14_5"]["ram"].get("gb"),
                "dsxl_coder": generated["dsxl_coder"]["ram"].get("gb"),
                "handheld_hybrid": generated["handheld_hybrid"]["ram"].get("gb"),
            },
            "measurement_class": "MODELED_TARGET_RANGE",
        }
        out["storage"] = {
            "status": "aggregate",
            "members": {
                "student_14_5": generated["student_14_5"]["storage"],
                "dsxl_coder": generated["dsxl_coder"]["storage"],
                "handheld_hybrid": generated["handheld_hybrid"]["storage"],
            },
            "measurement_class": "MODELED_TARGET_RANGE",
        }
        out["exact_mpns"] = {
            m: (generated[m].get("exact_mpns") or {}) for m in members
        }
        out["display_outputs"] = [
            {"id": "student", "role": "member"},
            {"id": "dsxl_top", "role": "member"},
            {"id": "dsxl_bottom", "role": "member"},
            {"id": "handheld", "role": "member"},
            {"id": "dock_external", "role": "member"},
        ]
        out["display_geometry"] = {"status": "multi_device"}
        out["touch"] = True
        out["input_capabilities"] = {"multi_device": True, "rings": True}
        out["audio_capabilities"] = {"multi_device": True}
        out["network_capabilities"] = {"5g_a_sim": "FUTURE", "ntn_sim": "FUTURE"}
        out["cellular_target"] = {"status": "FUTURE"}
        out["dock_capabilities"] = {"supported": True}
        out["ring_capabilities"] = {"supported": True, "count": 2}
        out["AI_capabilities"] = {"local": True, "shared_context": "FUTURE"}
        out["fidelity_level"] = "VF1"
        out["status_notes"] = [
            "Architecture present; full simultaneous sim is LAB-FUTURE — not claimed complete",
            "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE remains false",
        ]
        return out

    raise KeyError(f"unsupported profile_id for sync: {profile_id}")


def profile_path(profile_id: str, *, profiles_dir: Path | None = None) -> Path:
    return (profiles_dir or PROFILES_DIR) / f"{profile_id}.json"


def sync_profiles(
    *,
    profiles_dir: Path | None = None,
    truth: dict[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    truth = truth or load_accepted_hardware_truth()
    profiles_dir = profiles_dir or PROFILES_DIR
    written: list[str] = []
    generated: dict[str, Any] = {}
    for pid in CATALOG:
        doc = generate_profile(pid, truth=truth)
        generated[pid] = doc
        if write:
            path = profile_path(pid, profiles_dir=profiles_dir)
            path.write_text(_canonical(doc), encoding="utf-8")
            written.append(pid)
    return {
        "ok": True,
        "written": written,
        "catalog": list(CATALOG),
        "hardware_repo_sha": (truth.get("hardware_repo") or {}).get("pinned_sha"),
        "SILICON_EXACT_EMULATION": False,
        "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
    }


def _extract_drift_view(doc: dict[str, Any]) -> dict[str, Any]:
    return {k: doc.get(k) for k in DRIFT_KEYS}


def verify_profiles(
    *,
    profiles_dir: Path | None = None,
    truth: dict[str, Any] | None = None,
) -> dict[str, Any]:
    truth = truth or load_accepted_hardware_truth()
    profiles_dir = profiles_dir or PROFILES_DIR
    failures: list[dict[str, Any]] = []
    checked: list[str] = []
    for pid in CATALOG:
        path = profile_path(pid, profiles_dir=profiles_dir)
        if not path.exists():
            failures.append({"profile_id": pid, "error": "missing_profile_file"})
            continue
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        expected = generate_profile(pid, truth=truth)
        checked.append(pid)
        if on_disk.get("SILICON_EXACT_EMULATION") is not False:
            failures.append({"profile_id": pid, "error": "SILICON_EXACT_EMULATION_not_false"})
        disk_view = _extract_drift_view(on_disk)
        exp_view = _extract_drift_view(expected)
        if disk_view != exp_view:
            failures.append(
                {
                    "profile_id": pid,
                    "error": "drift",
                    "disk": disk_view,
                    "expected": exp_view,
                }
            )
        # Extra MPN sanity: compute MPN must match truth when present
        prod = (truth.get("products") or {}).get(pid)
        if prod and (prod.get("compute") or {}).get("mpn"):
            want = prod["compute"]["mpn"]
            got = ((on_disk.get("compute") or {}).get("mpn") or (on_disk.get("exact_mpns") or {}).get("compute"))
            if got != want:
                failures.append(
                    {
                        "profile_id": pid,
                        "error": "mpn_mismatch",
                        "want": want,
                        "got": got,
                    }
                )
    ok = not failures
    return {
        "ok": ok,
        "checked": checked,
        "failures": failures,
        "hardware_repo_sha": (truth.get("hardware_repo") or {}).get("pinned_sha"),
        "SILICON_EXACT_EMULATION": False,
        "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
        "gate": "PASS" if ok else "FAIL_STALE_RAM_STORAGE_OR_MPN",
    }


def diff_profiles(
    *,
    profiles_dir: Path | None = None,
    truth: dict[str, Any] | None = None,
) -> dict[str, Any]:
    truth = truth or load_accepted_hardware_truth()
    profiles_dir = profiles_dir or PROFILES_DIR
    diffs: dict[str, Any] = {}
    for pid in CATALOG:
        path = profile_path(pid, profiles_dir=profiles_dir)
        expected = generate_profile(pid, truth=truth)
        if not path.exists():
            diffs[pid] = {"status": "missing", "expected_drift_view": _extract_drift_view(expected)}
            continue
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        disk_view = _extract_drift_view(on_disk)
        exp_view = _extract_drift_view(expected)
        if disk_view != exp_view:
            diffs[pid] = {"status": "drift", "disk": disk_view, "expected": exp_view}
        else:
            diffs[pid] = {"status": "match"}
    return {
        "ok": all(v.get("status") == "match" for v in diffs.values()),
        "diffs": diffs,
        "SILICON_EXACT_EMULATION": False,
    }


def refresh_truth_from_sibling(hardware_repo: Path) -> dict[str, Any]:
    """Optional refresh helper — reads sibling SHA; does not invent MPNs.

    Returns current vendored truth annotated with observed sibling SHA for operators.
    Automated rewrite of MPNs from markdown is intentionally out of scope: the
    committed snapshot is the CI authority after human-reviewed sync.
    """
    sha = None
    git_dir = hardware_repo / ".git"
    if git_dir.exists():
        import subprocess

        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=hardware_repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            sha = proc.stdout.strip()
    truth = load_accepted_hardware_truth()
    return {
        "ok": True,
        "vendored_sha": (truth.get("hardware_repo") or {}).get("pinned_sha"),
        "sibling_sha": sha,
        "sibling_path": str(hardware_repo),
        "note": (
            "Update accepted_hardware_truth.json by reviewed edit when sibling SHA advances; "
            "then run gunnchctl profile sync"
        ),
        "SILICON_EXACT_EMULATION": False,
    }


# Keep load_profile import used for type/check side effects in tests
__all__ = [
    "generate_profile",
    "sync_profiles",
    "verify_profiles",
    "diff_profiles",
    "refresh_truth_from_sibling",
    "load_profile",
]
