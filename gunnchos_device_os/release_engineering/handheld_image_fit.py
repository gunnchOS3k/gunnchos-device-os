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
# Below this compressed size, rootfs is treated as package-stub (not production-intent).
STUB_COMPRESSED_CEILING_BYTES = 2 * 1024 * 1024

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
    "silicon-exact, not signed production shipping. When payload_class is "
    "production_intent_digital, rootfs embeds Alpine minirootfs + gunnchOS "
    "userspace for MLP-class digital slot-fit — still SHIPPING_IMAGE=false and "
    "PRODUCTION_RELEASE_CLAIMED=false always."
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
    payload = build_manifest.get("payload") or {}
    payload_class = (
        build_manifest.get("payload_class")
        or payload.get("payload_class")
        or "unknown"
    )
    stub_like = compressed < STUB_COMPRESSED_CEILING_BYTES
    production_intent = (
        payload_class == "production_intent_digital" and not stub_like
    )
    return {
        "ok": True,
        "realm_dir": realm_dir,
        "realm_id": build_manifest.get("realm_id") or realm_dir.upper(),
        "status": build_manifest.get("status"),
        "signing_realm": build_manifest.get("signing_realm"),
        "payload_class": payload_class,
        "payload_profile": payload.get("payload_profile"),
        "SHIPPING_IMAGE": bool(build_manifest.get("SHIPPING_IMAGE", False)),
        "production_intent_digital": production_intent,
        "stub_like": stub_like,
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
        "alpine_minirootfs": (payload.get("alpine_minirootfs") or None),
        "userspace_trees": payload.get("userspace_trees") or [],
    }


def _measure_boot_reference(repo_root: Path) -> dict[str, Any]:
    """Measure shared boot reference for slot composition.

    Kernel/initramfs binaries are gitignored and may be rebuilt non-deterministically
    during CI (cpio timestamps). Prefer committed MANIFEST.json artifact metadata for
    reproducible IMAGE_FIT_MANIFEST evidence; fall back to on-disk files when needed.
    """
    art = repo_root / "os_build" / "bootable_reference" / "artifacts"
    kernel = art / "vmlinuz-virt"
    initramfs = art / "gunnchos-ref-initramfs.cpio.gz"
    manifest_path = art / "MANIFEST.json"
    committed: dict[str, Any] = {}
    if manifest_path.is_file():
        try:
            committed = (
                json.loads(manifest_path.read_text(encoding="utf-8")).get("artifacts") or {}
            )
        except Exception:
            committed = {}
    out: dict[str, Any] = {
        "kind": "shared_bootable_reference",
        "note": (
            "Shared DEV/QEMU reference — not realm-specific compiled binaries. "
            "Sizes/hashes prefer committed bootable_reference MANIFEST.json because "
            "vmlinuz*/*.cpio* are gitignored and CI rebuilds can drift by tens of bytes."
        ),
        "size_source": "committed_manifest" if committed else "on_disk_or_missing",
    }
    total = 0
    for key, path in (("kernel", kernel), ("initramfs", initramfs)):
        meta = committed.get(key) or {}
        rel = str(path.relative_to(repo_root))
        if isinstance(meta, dict) and meta.get("size_bytes") is not None:
            nbytes = int(meta["size_bytes"])
            total += nbytes
            entry: dict[str, Any] = {
                "path": meta.get("path") or rel,
                "sha256": meta.get("sha256"),
                "bytes": nbytes,
                "gib": _gib(nbytes),
                "present": path.is_file(),
                "size_source": "committed_manifest",
            }
            if path.is_file():
                entry["on_disk_bytes"] = path.stat().st_size
            out[key] = entry
        elif path.is_file():
            nbytes = path.stat().st_size
            total += nbytes
            out[key] = {
                "path": rel,
                "sha256": _sha256_file(path),
                "bytes": nbytes,
                "gib": _gib(nbytes),
                "present": True,
                "size_source": "on_disk",
            }
        else:
            out[key] = {"path": rel, "present": False, "size_source": "missing"}
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
    intent = bool(realm.get("production_intent_digital"))
    honesty = (
        "Numeric fit of production-intent digital rootfs (Alpine + gunnchOS userspace) "
        "+ shared reference boot vs Outcome A budget. Not physical flash; "
        "SHIPPING_IMAGE=false."
        if intent
        else (
            "Numeric fit of CURRENT digital realm stub + shared reference boot only. "
            "Not proof of full MLP/production A/B disk-image fit."
        )
    )
    return {
        "slot": slot,
        "budget_gib": budget_gib,
        "budget_bytes": budget_bytes,
        "realm_id": realm.get("realm_id"),
        "payload_class": realm.get("payload_class"),
        "production_intent_digital": intent,
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
        "honesty": honesty,
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

    # A/B slots measure unsigned production-intent definition (identical-slot assumption).
    slot_a = _compose_slot_proxy(
        production, boot, slot="slot_a", budget_gib=SLOT_BUDGETS_GIB["slot_a"]
    )
    slot_b = _compose_slot_proxy(
        production, boot, slot="slot_b", budget_gib=SLOT_BUDGETS_GIB["slot_b"]
    )
    slot_b["note"] = (
        "Proxy uses PRODUCTION_SHIPPING_IMAGE_DEFINITION composed size for both "
        "A and B (identical-slot A/B update payload assumption)."
    )
    slot_recovery = _compose_slot_proxy(
        recovery, boot, slot="recovery", budget_gib=SLOT_BUDGETS_GIB["recovery"]
    )

    # EVT/factory reported for comparison.
    evt_proxy = _compose_slot_proxy(
        evt, boot, slot="evt_engineering_report_only", budget_gib=SLOT_BUDGETS_GIB["slot_a"]
    )
    factory_proxy = _compose_slot_proxy(
        factory, boot, slot="factory_provisioning_report_only", budget_gib=SLOT_BUDGETS_GIB["slot_a"]
    )

    all_realms_ok = all(r.get("ok") for r in realms.values())
    boot_ok = bool(
        (boot.get("kernel") or {}).get("present") and (boot.get("initramfs") or {}).get("present")
    )
    numeric_fit = all(s["fits_budget"] for s in (slot_a, slot_b, slot_recovery)) and all_realms_ok and boot_ok
    any_production_claimed = any(r.get("PRODUCTION_RELEASE_CLAIMED") for r in realms.values())
    any_shipping_claimed = any(r.get("SHIPPING_IMAGE") for r in realms.values())
    stub_like = any(bool(r.get("stub_like")) for r in realms.values() if r.get("ok"))
    production_intent_ok = all(
        bool(r.get("production_intent_digital")) for r in (production, recovery) if r.get("ok")
    ) and all_realms_ok

    if (
        production_intent_ok
        and numeric_fit
        and not stub_like
        and not any_production_claimed
        and not any_shipping_claimed
    ):
        npi_closure_met = True
        npi_status = "CLOSE"
        verdict = "PASS_PRODUCTION_INTENT_DIGITAL_FIT"
        npi_reason = (
            "Production-intent digital A/B (production_shipping_image_definition) and "
            "recovery rootfs tarballs embed Alpine minirootfs + gunnchOS userspace, "
            "exceed stub ceiling, and compose with shared boot reference under Outcome A "
            "5.0/5.0/2.0 GiB budgets with positive margin. Propose NPI "
            "NPI_DEFECT-HANDHELD-IMAGE-SLOT-FIT-001 CLOSE for digital slot-fit only. "
            "SHIPPING_IMAGE=false; PRODUCTION_RELEASE_CLAIMED=false; no physical flash."
        )
    elif stub_like or not production_intent_ok:
        npi_closure_met = False
        npi_status = "OPEN"
        verdict = "FAIL_STUB_REALM_NOT_MLP"
        npi_reason = (
            "Measured realm rootfs tarballs exist but remain package-stub or lack "
            "production_intent_digital Alpine+userspace payloads. Keep "
            "NPI_DEFECT-HANDHELD-IMAGE-SLOT-FIT-001 OPEN."
        )
    else:
        npi_closure_met = False
        npi_status = "OPEN"
        verdict = "FAIL_PRODUCTION_INTENT_OVER_BUDGET"
        npi_reason = (
            "Production-intent digital payloads exist but composed sizes exceed Outcome A "
            "slot budgets (or boot/realm artifacts missing). Keep NPI OPEN and reopen "
            "architecture without inventing larger eMMC SKUs — retain Outcome A + microSD "
            "or reduce onboard payload."
        )

    arch_next = (
        [
            "Hardware may CLOSE NPI_DEFECT-HANDHELD-IMAGE-SLOT-FIT-001 on digital evidence "
            "when consuming this IMAGE_FIT_MANIFEST (margin_gib > 0, production_intent)",
            "Do not claim SHIPPING_IMAGE, physical flash, or PRODUCTION_RELEASE",
            "Retain Outcome A (32GB system + microSD for MLP user content); no invented eMMC SKU",
            "Optional: refresh EVT/factory comparison sizes on subsequent remeasures",
        ]
        if npi_closure_met
        else [
            "Grow realm builder toward production-intent rootfs (Alpine + real userspace) and remeasure",
            "Publish refreshed IMAGE_FIT_MANIFEST.json with margin_gib > 0 for slot_a/slot_b/recovery",
            "Hardware remodel may CLOSE only when production-intent measured images exist",
            "If measured production-intent images exceed onboard usable after reserves, reopen "
            "architecture (still without inventing eMMC SKUs)",
        ]
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
        "SHIPPING_IMAGE": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "slot_budgets_gib": dict(SLOT_BUDGETS_GIB),
        "shared_bootable_reference": boot,
        "realms": realms,
        "slot_fit": {
            "slot_a": slot_a,
            "slot_b": slot_b,
            "recovery": slot_recovery,
            "evt_engineering_report_only": evt_proxy,
            "factory_provisioning_report_only": factory_proxy,
        },
        "fit_assessment": {
            "realm_rootfs_artifacts_present": all_realms_ok,
            "shared_boot_reference_present": boot_ok,
            "current_digital_realm_numeric_fit": numeric_fit,
            "production_mlp_disk_image_present": False,
            "production_intent_digital_present": production_intent_ok,
            "production_shipping_status": production.get("status"),
            "production_shipping_unsigned": production.get("signing_realm") in (None, "none")
            or production.get("status") == "NOT_RELEASED",
            "stub_like_rootfs_payloads": stub_like,
            "any_PRODUCTION_RELEASE_CLAIMED_true": any_production_claimed,
            "any_SHIPPING_IMAGE_true": any_shipping_claimed,
            "production_image_fit_verdict": verdict,
            "production_image_fit_reason": npi_reason,
        },
        "npi": {
            "defect_id": "NPI_DEFECT-HANDHELD-IMAGE-SLOT-FIT-001",
            "recommended_status": npi_status,
            "closure_gate_met": npi_closure_met,
            "closure_gate_reason": npi_reason,
            "closure_scope": (
                "digital_production_intent_slot_fit_only" if npi_closure_met else None
            ),
            "architecture_change_proposal": {
                "retain_outcome_a": True,
                "invent_larger_emmc_sku": False,
                "microsd_required_for_mlp_user_content": True,
                "architecture_change_required": bool(
                    verdict == "FAIL_PRODUCTION_INTENT_OVER_BUDGET"
                ),
                "next_steps": arch_next,
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
            "production_def_rootfs_uncompressed": (production.get("rootfs_tarball") or {}).get(
                "uncompressed_file_gib"
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
