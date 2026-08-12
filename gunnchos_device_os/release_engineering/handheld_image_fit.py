"""Handheld Outcome A image-slot fit measurement (digital evidence only).

Emits machine-readable IMAGE_FIT_MANIFEST.json from built realm rootfs
tarballs + shared bootable_reference kernel/initramfs. Does not invent
disk images, larger eMMC SKUs, or production release claims.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import tarfile
import time
from pathlib import Path
from typing import Any

GIB = 1024**3

# Outcome A onboard slot budgets (GiB) — hardware NPI contract.
SLOT_BUDGETS_GIB = {
    "slot_a": 5.0,
    "slot_b": 5.0,
    "recovery": 2.0,
}

# Realms measured for Handheld profile fit evidence.
HANDHELD_REALMS = (
    "evt_engineering_image",
    "factory_provisioning_image",
    "recovery_image",
    "production_shipping_image_definition",
)

SCHEMA = "gunnchos.device_os.handheld_image_fit_manifest.v1"
CLAIM_BOUNDARY = (
    "Digital measurement of WP-013 realm rootfs.tar.gz artifacts plus shared "
    "bootable_reference kernel/initramfs. Not a physical eMMC flash image, not "
    "silicon-exact, not signed production shipping. Realm rootfs payloads are "
    "release-engineering package stubs (service units + optional Python tree), "
    "not a full MLP userspace. PRODUCTION_RELEASE_CLAIMED=false always."
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _gib(nbytes: int) -> float:
    return round(nbytes / GIB, 9)


def _git_head(repo_root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def _uncompressed_tar_bytes(tar_gz: Path) -> tuple[int, int]:
    with tarfile.open(tar_gz, "r:gz") as tf:
        members = tf.getmembers()
        unc = sum(m.size for m in members if m.isfile())
        return unc, sum(1 for m in members if m.isfile())


def _measure_realm(repo_root: Path, realm_dir: str) -> dict[str, Any]:
    art = repo_root / "os_build" / "realm_images" / realm_dir / "artifacts"
    rootfs = art / "rootfs.tar.gz"
    manifest_path = art / "BUILD_MANIFEST.json"
    if not rootfs.is_file():
        return {
            "ok": False,
            "realm_dir": realm_dir,
            "error": "rootfs_tarball_missing",
            "path": str(rootfs.relative_to(repo_root)),
        }
    compressed = rootfs.stat().st_size
    uncompressed, file_count = _uncompressed_tar_bytes(rootfs)
    build_manifest: dict[str, Any] = {}
    if manifest_path.is_file():
        build_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "ok": True,
        "realm_dir": realm_dir,
        "realm_id": build_manifest.get("realm_id") or realm_dir.upper(),
        "status": build_manifest.get("status"),
        "signing_realm": build_manifest.get("signing_realm"),
        "PRODUCTION_RELEASE_CLAIMED": bool(
            build_manifest.get("PRODUCTION_RELEASE_CLAIMED", False)
        ),
        "rootfs_tarball": {
            "path": str(rootfs.relative_to(repo_root)),
            "sha256": _sha256_file(rootfs),
            "compressed_bytes": compressed,
            "compressed_gib": _gib(compressed),
            "uncompressed_file_bytes": uncompressed,
            "uncompressed_file_gib": _gib(uncompressed),
            "file_count": file_count,
        },
        "build_manifest_path": (
            str(manifest_path.relative_to(repo_root)) if manifest_path.is_file() else None
        ),
        "image_hash": build_manifest.get("image_hash"),
    }


def _measure_boot_reference(repo_root: Path) -> dict[str, Any]:
    art = repo_root / "os_build" / "bootable_reference" / "artifacts"
    kernel = art / "vmlinuz-virt"
    initramfs = art / "gunnchos-ref-initramfs.cpio.gz"
    out: dict[str, Any] = {
        "kind": "shared_bootable_reference",
        "note": "Shared DEV/QEMU reference — not realm-specific compiled binaries.",
    }
    total = 0
    for key, path in (("kernel", kernel), ("initramfs", initramfs)):
        if path.is_file():
            nbytes = path.stat().st_size
            total += nbytes
            out[key] = {
                "path": str(path.relative_to(repo_root)),
                "sha256": _sha256_file(path),
                "bytes": nbytes,
                "gib": _gib(nbytes),
                "present": True,
            }
        else:
            out[key] = {"path": str(path.relative_to(repo_root)), "present": False}
    out["combined_bytes"] = total
    out["combined_gib"] = _gib(total)
    return out


def _compose_slot_proxy(
    realm: dict[str, Any],
    boot: dict[str, Any],
    *,
    slot: str,
    budget_gib: float,
) -> dict[str, Any]:
    rootfs_unc = int((realm.get("rootfs_tarball") or {}).get("uncompressed_file_bytes") or 0)
    boot_bytes = int(boot.get("combined_bytes") or 0)
    composed = rootfs_unc + boot_bytes
    budget_bytes = int(budget_gib * GIB)
    margin = budget_bytes - composed
    return {
        "slot": slot,
        "budget_gib": budget_gib,
        "budget_bytes": budget_bytes,
        "realm_id": realm.get("realm_id"),
        "composition": {
            "rootfs_uncompressed_file_bytes": rootfs_unc,
            "shared_kernel_initramfs_bytes": boot_bytes,
            "method": "uncompressed_rootfs_files + shared_bootable_reference_kernel_initramfs",
        },
        "composed_bytes": composed,
        "composed_gib": _gib(composed),
        "margin_bytes": margin,
        "margin_gib": _gib(margin),
        "fits_budget": margin > 0,
        "honesty": (
            "Numeric fit of CURRENT digital realm stub + shared reference boot only. "
            "Not proof of full MLP/production A/B disk-image fit."
        ),
    }


def build_handheld_image_fit_manifest(repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = Path(repo_root or _repo_root())
    boot = _measure_boot_reference(repo_root)
    realms: dict[str, Any] = {}
    for realm_dir in HANDHELD_REALMS:
        realms[realm_dir] = _measure_realm(repo_root, realm_dir)

    evt = realms["evt_engineering_image"]
    factory = realms["factory_provisioning_image"]
    recovery = realms["recovery_image"]
    production = realms["production_shipping_image_definition"]

    slot_a = _compose_slot_proxy(evt, boot, slot="slot_a", budget_gib=SLOT_BUDGETS_GIB["slot_a"])
    # A/B identical size assumption for current digital EVT candidate.
    slot_b = _compose_slot_proxy(evt, boot, slot="slot_b", budget_gib=SLOT_BUDGETS_GIB["slot_b"])
    slot_b["note"] = "Proxy uses EVT composed size for both A and B (identical-slot assumption)."
    slot_recovery = _compose_slot_proxy(
        recovery, boot, slot="recovery", budget_gib=SLOT_BUDGETS_GIB["recovery"]
    )

    # Factory + production-definition are reported; production is NOT_RELEASED unsigned.
    factory_proxy = _compose_slot_proxy(
        factory, boot, slot="factory_provisioning_report_only", budget_gib=SLOT_BUDGETS_GIB["slot_a"]
    )
    production_proxy = _compose_slot_proxy(
        production,
        boot,
        slot="production_shipping_definition_unsigned",
        budget_gib=SLOT_BUDGETS_GIB["slot_a"],
    )

    all_realms_ok = all(r.get("ok") for r in realms.values())
    boot_ok = bool((boot.get("kernel") or {}).get("present") and (boot.get("initramfs") or {}).get("present"))
    numeric_fit = all(
        s["fits_budget"] for s in (slot_a, slot_b, slot_recovery)
    ) and all_realms_ok and boot_ok
    any_production_claimed = any(r.get("PRODUCTION_RELEASE_CLAIMED") for r in realms.values())

    # Honest NPI gate: stub realm tarballs are necessary evidence but not closure.
    stub_like = all(
        int((r.get("rootfs_tarball") or {}).get("compressed_bytes") or 0) < 2 * 1024 * 1024
        for r in realms.values()
        if r.get("ok")
    )
    npi_closure_met = False
    npi_reason = (
        "Measured EVT/factory/recovery/production-definition rootfs tarballs exist with "
        "sha256/bytes and positive numeric margin vs Outcome A 5.0/5.0/2.0 GiB budgets, "
        "but payloads remain package-stub digital artifacts (<2 MiB compressed each), not "
        "full MLP/production A/B disk images. Keep NPI_DEFECT-HANDHELD-IMAGE-SLOT-FIT-001 OPEN."
    )

    return {
        "schema": SCHEMA,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "device_os_tip": _git_head(repo_root),
        "measured_against_main_tip": None,  # filled by emit script / CI when known
        "sku_profile": "handheld_hybrid",
        "architecture_outcome": "A",
        "architecture_title": "32GB_SYSTEM_ONLY_PLUS_SUPPORTED_MICROSD",
        "larger_emmc_sku_invented": False,
        "PRODUCTION_RELEASE_CLAIMED": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "slot_budgets_gib": dict(SLOT_BUDGETS_GIB),
        "shared_bootable_reference": boot,
        "realms": realms,
        "slot_fit": {
            "slot_a": slot_a,
            "slot_b": slot_b,
            "recovery": slot_recovery,
            "factory_provisioning_report_only": factory_proxy,
            "production_shipping_definition_unsigned": production_proxy,
        },
        "fit_assessment": {
            "realm_rootfs_artifacts_present": all_realms_ok,
            "shared_boot_reference_present": boot_ok,
            "current_digital_realm_numeric_fit": numeric_fit,
            "production_mlp_disk_image_present": False,
            "production_shipping_status": production.get("status"),
            "production_shipping_unsigned": production.get("signing_realm") in (None, "none")
            or production.get("status") == "NOT_RELEASED",
            "stub_like_rootfs_payloads": stub_like,
            "any_PRODUCTION_RELEASE_CLAIMED_true": any_production_claimed,
            "production_image_fit_verdict": "FAIL_STUB_REALM_NOT_MLP",
            "production_image_fit_reason": npi_reason,
        },
        "npi": {
            "defect_id": "NPI_DEFECT-HANDHELD-IMAGE-SLOT-FIT-001",
            "recommended_status": "OPEN",
            "closure_gate_met": npi_closure_met,
            "closure_gate_reason": npi_reason,
            "architecture_change_proposal": {
                "retain_outcome_a": True,
                "invent_larger_emmc_sku": False,
                "microsd_required_for_mlp_user_content": True,
                "next_steps": [
                    "Grow realm builder toward production-intent rootfs (real userspace payload, not service-unit stubs alone) and remeasure",
                    "Publish refreshed IMAGE_FIT_MANIFEST.json with margin_gib > 0 for slot_a/slot_b/recovery",
                    "Hardware remodel may CLOSE only when production-intent measured images exist — contracts/stubs insufficient",
                    "If measured production-intent images exceed onboard usable after reserves, reopen architecture (still without inventing eMMC SKUs)",
                ],
            },
        },
        "sizes_summary_gib": {
            "evt_rootfs_compressed": (evt.get("rootfs_tarball") or {}).get("compressed_gib"),
            "evt_rootfs_uncompressed": (evt.get("rootfs_tarball") or {}).get("uncompressed_file_gib"),
            "factory_rootfs_compressed": (factory.get("rootfs_tarball") or {}).get("compressed_gib"),
            "recovery_rootfs_compressed": (recovery.get("rootfs_tarball") or {}).get("compressed_gib"),
            "production_def_rootfs_compressed": (production.get("rootfs_tarball") or {}).get(
                "compressed_gib"
            ),
            "slot_a_composed": slot_a["composed_gib"],
            "slot_b_composed": slot_b["composed_gib"],
            "recovery_composed": slot_recovery["composed_gib"],
            "slot_a_margin": slot_a["margin_gib"],
            "slot_b_margin": slot_b["margin_gib"],
            "recovery_margin": slot_recovery["margin_gib"],
            "shared_boot_combined": boot.get("combined_gib"),
        },
    }


def write_handheld_image_fit_manifest(
    repo_root: Path | None = None,
    *,
    out_path: Path | None = None,
) -> dict[str, Any]:
    repo_root = Path(repo_root or _repo_root())
    manifest = build_handheld_image_fit_manifest(repo_root)
    out = Path(out_path or (repo_root / "artifacts" / "handheld_image_fit" / "IMAGE_FIT_MANIFEST.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        manifest["_written_to"] = str(out.relative_to(repo_root))
    except ValueError:
        manifest["_written_to"] = str(out)
    return manifest
