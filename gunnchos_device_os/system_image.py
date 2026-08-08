"""Reproducible digital system image path for gunnchOS.

Builds a deterministic DEV factory image *bundle* (not a bootable disk image):
kernel/bootloader/init notes, driver classification, filesystem layout,
compositor/shell stubs, package list, sandbox/updater/recovery hooks,
version manifest, SBOM, provenance, and VM/emulation target metadata.

Honest token: GUNNCHOS_REPRODUCIBLE_SYSTEM_IMAGE_DIGITAL_PASS is emitted only
when the digital bundle validates (deterministic hashes, required artifacts,
DEV-realm signing stub). Never claims production keys, physical boot, or
FULL_OPERATIONAL_PRODUCT.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
import hashlib
import json
import tempfile


CLAIM_BOUNDARY = (
    "Digital reproducible system-image *path* only. Produces a DEV factory "
    "bundle with manifests/SBOM/provenance — not a bootable ISO/IMG, not "
    "hardware-validated, no production signing keys, not FULL_OPERATIONAL_PRODUCT."
)

TOKEN_DIGITAL_PASS = "GUNNCHOS_REPRODUCIBLE_SYSTEM_IMAGE_DIGITAL_PASS"
TOKEN_PHYSICAL_PENDING = "GUNNCHOS_PHYSICAL_SYSTEM_IMAGE_PENDING"

# Frozen digital content — changing these intentionally changes hashes.
KERNEL_CHOICE = {
    "family": "linux",
    "track": "LTS",
    "preferred_version_series": "6.6.x",
    "config_notes": [
        "Enable cgroups v2, namespaces, seccomp, overlayfs for sandbox path",
        "DRM/KMS for dual-display DS-XL; keep vendor blobs out of DEV image",
        "Disable unused wireless firmwares in minimal DEV profile",
        "CONFIG_IKCONFIG_PROC=y for config auditability in DEV images",
    ],
    "claim": "Kernel *choice and config notes* only — kernel binary not built in this track",
}

BOOTLOADER = {
    "primary": "UEFI GRUB2 (x86_64 DEV/VM)",
    "secondary": "U-Boot (aarch64 hardware track — not produced here)",
    "secure_boot": "DEV shim stub only — production keys forbidden in this realm",
    "claim": "Bootloader path documented; no signed production boot chain",
}

INIT_SYSTEM = {
    "init": "systemd",
    "targets": ["multi-user.target", "graphical.target"],
    "gunnchos_units": [
        "gunnchos-runtime.service",
        "gunnchos-updater.service",
        "gunnchos-fleet-agent.service",
        "gunnchos-recovery.target",
    ],
    "claim": "Unit stubs only — not a shipping initramfs",
}

DRIVER_CLASSES = {
    "required_open": ["virtio", "drm-generic", "input-evdev", "usbhid"],
    "optional_open": ["iwlwifi-open-fw", "r8169"],
    "deferred_vendor": ["gpu-vendor-blob", "modem-vendor-fw"],
    "policy": "DEV image includes only open/required classes; vendor blobs deferred",
}

FILESYSTEM_LAYOUT = {
    "/": "rootfs erofs or squashfs (immutable)",
    "/boot": "ESP + kernel/initrd stubs",
    "/var": "mutable overlay",
    "/var/lib/gunnchos": "runtime persistence",
    "/etc/gunnchos": "policy + profiles",
    "/opt/gunnchos": "shell + packages",
    "/recovery": "recovery ramdisk mount",
    "ab_slots": ["slot_a", "slot_b"],
}

COMPOSITOR_SHELL = {
    "compositor": "wlroots-based stub (not built)",
    "shell": "gunnchos-shell stub",
    "dual_screen": "DS-XL role framework wired in userspace (dual_screen.py)",
    "claim": "Stubs + userspace role model only — not a proven compositor",
}

PACKAGES = [
    {"name": "gunnchos-runtime", "version": "0.3.0-dev", "kind": "os-service"},
    {"name": "gunnchos-launcher-mock", "version": "0.2.0-alpha", "kind": "shell"},
    {"name": "gunnchos-sandbox-policy", "version": "0.1.0", "kind": "policy"},
    {"name": "gunnchos-updater", "version": "0.1.0", "kind": "ota"},
    {"name": "gunnchos-recovery", "version": "0.1.0", "kind": "recovery"},
    {"name": "gunnchos-fleet-agent", "version": "0.1.0-dev", "kind": "fleet"},
]

SANDBOX_HOOK = {
    "engine": "sandbox_policy.py",
    "enforcement": "software_policy",
    "kernel_path": "namespaces/seccomp planned — not claimed enforced in DEV bundle",
}

UPDATER_HOOK = {
    "engine": "ota_state_machine.py",
    "slots": ["a", "b"],
    "signing": "DEV_HMAC_STUB_ONLY",
}

RECOVERY_HOOK = {
    "engine": "boot.recovery",
    "target": "gunnchos-recovery.target",
    "physical_claim": "GUNNCHOS_PHYSICAL_BOOT_PENDING",
}

VM_EMULATION_TARGET = {
    "primary": "qemu-system-x86_64",
    "machine": "q35",
    "firmware": "OVMF (UEFI)",
    "status": "documented_target",
    "full_system_smoke": "BLOCKED_TOOLCHAIN until QEMU harness wired in CI",
    "alternate": "Docker os_build/image_prototype kiosk (userspace only)",
}


def _canonical_json(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _dev_hmac(message: bytes, key: bytes) -> str:
    """DEV-realm HMAC stub — intentionally not a production KMS signature."""
    return hashlib.sha256(key + b"|" + message).hexdigest()


DEV_REALM_KEY_MATERIAL = b"gunnchos-dev-factory-image-realm-v1-NOT-PRODUCTION"


@dataclass
class ImageBuildRequest:
    version: str = "0.3.0-dev"
    channel: str = "dev"
    build_id: str = "digital-repro-001"
    sku: str = "ds_xl_coder"
    out_dir: str = "os_build/reproducible_system_image/artifacts"


@dataclass
class ReproducibleImageBuilder:
    """Deterministic DEV factory image bundle builder."""

    request: ImageBuildRequest = field(default_factory=ImageBuildRequest)

    def blueprint(self) -> dict[str, Any]:
        return {
            "kernel": KERNEL_CHOICE,
            "bootloader": BOOTLOADER,
            "init": INIT_SYSTEM,
            "drivers": DRIVER_CLASSES,
            "filesystem": FILESYSTEM_LAYOUT,
            "compositor_shell": COMPOSITOR_SHELL,
            "packages": PACKAGES,
            "sandbox": SANDBOX_HOOK,
            "updater": UPDATER_HOOK,
            "recovery": RECOVERY_HOOK,
            "vm_emulation_target": VM_EMULATION_TARGET,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def version_manifest(self, content_digest: str) -> dict[str, Any]:
        return {
            "product": "gunnchOS",
            "version": self.request.version,
            "channel": self.request.channel,
            "build_id": self.request.build_id,
            "sku": self.request.sku,
            "realm": "DEV",
            "content_digest_sha256": content_digest,
            "bootable": False,
            "iso_built": False,
            "production_keys_used": False,
            "components": {
                "runtime": "gunnchos_device_os.runtime",
                "sandbox": "gunnchos_device_os.sandbox_policy",
                "updater": "gunnchos_device_os.ota_state_machine",
                "recovery": "gunnchos_device_os.boot.recovery",
                "dual_screen": "gunnchos_device_os.dual_screen",
            },
            "claims": {
                "full_operational_product": False,
                "hardware_validated": False,
                "production_signed": False,
            },
        }

    def sbom(self) -> dict[str, Any]:
        components = []
        for pkg in PACKAGES:
            components.append(
                {
                    "type": "library",
                    "name": pkg["name"],
                    "version": pkg["version"],
                    "purl": f"pkg:generic/{pkg['name']}@{pkg['version']}",
                    "properties": [{"name": "gunnchos:kind", "value": pkg["kind"]}],
                }
            )
        # Include Python package self-reference
        components.append(
            {
                "type": "library",
                "name": "gunnchos_device_os",
                "version": "0.1.0-evt1-alpha",
                "purl": "pkg:generic/gunnchos_device_os@0.1.0-evt1-alpha",
            }
        )
        return {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "version": 1,
            "metadata": {
                "component": {
                    "type": "firmware",
                    "name": "gunnchos-dev-factory-image",
                    "version": self.request.version,
                },
                "properties": [
                    {"name": "gunnchos:realm", "value": "DEV"},
                    {"name": "gunnchos:production_keys", "value": "false"},
                ],
            },
            "components": components,
        }

    def provenance(self, artifact_hashes: dict[str, str]) -> dict[str, Any]:
        return {
            "predicateType": "gunnchos.dev.image.provenance.v1",
            "predicate": {
                "builder": {
                    "id": "gunnchos_device_os.system_image.ReproducibleImageBuilder",
                    "realm": "DEV",
                },
                "invocation": asdict(self.request),
                "materials": artifact_hashes,
                "reproducible": True,
                "timestamp": "STATIC_FOR_REPRO",  # frozen for hash stability
                "notes": [
                    "Timestamp frozen to STATIC_FOR_REPRO for deterministic digests",
                    "Re-run builder must yield identical content_digest when inputs unchanged",
                ],
            },
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def factory_image_stub(self, content_digest: str) -> dict[str, Any]:
        return {
            "image_id": f"gunnchos-dev-factory-{self.request.build_id}",
            "realm": "DEV",
            "label": "DEV_SIGNED_NOT_PRODUCTION_FACTORY_IMAGE",
            "content_digest_sha256": content_digest,
            "slots": ["a", "b"],
            "bootloader": BOOTLOADER["primary"],
            "init": INIT_SYSTEM["init"],
            "packages": [p["name"] for p in PACKAGES],
            "production_keys_used": False,
            "bootable_disk_image": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def build(self, *, out_dir: str | Path | None = None) -> dict[str, Any]:
        root = Path(out_dir or self.request.out_dir)
        root.mkdir(parents=True, exist_ok=True)
        if root.parent.name == "reproducible_system_image":
            notes_dir = root.parent / "notes"
            stubs_dir = root.parent / "stubs"
        else:
            notes_dir = root / "notes"
            stubs_dir = root / "stubs"
        notes_dir.mkdir(parents=True, exist_ok=True)
        stubs_dir.mkdir(parents=True, exist_ok=True)

        blueprint = self.blueprint()
        # Write notes (human-readable, content also embedded in blueprint)
        (notes_dir / "KERNEL.md").write_text(
            "# Kernel choice (DEV digital path)\n\n"
            + json.dumps(KERNEL_CHOICE, indent=2)
            + "\n",
            encoding="utf-8",
        )
        (notes_dir / "BOOTLOADER.md").write_text(
            "# Bootloader path\n\n" + json.dumps(BOOTLOADER, indent=2) + "\n",
            encoding="utf-8",
        )
        (notes_dir / "INIT.md").write_text(
            "# Init system\n\n" + json.dumps(INIT_SYSTEM, indent=2) + "\n",
            encoding="utf-8",
        )
        (notes_dir / "DRIVERS.md").write_text(
            "# Driver classification\n\n" + json.dumps(DRIVER_CLASSES, indent=2) + "\n",
            encoding="utf-8",
        )
        (notes_dir / "FILESYSTEM.md").write_text(
            "# Filesystem layout\n\n" + json.dumps(FILESYSTEM_LAYOUT, indent=2) + "\n",
            encoding="utf-8",
        )
        (notes_dir / "VM_EMULATION.md").write_text(
            "# VM / emulation target\n\n" + json.dumps(VM_EMULATION_TARGET, indent=2) + "\n",
            encoding="utf-8",
        )
        (stubs_dir / "compositor_shell.json").write_text(
            json.dumps(COMPOSITOR_SHELL, indent=2) + "\n", encoding="utf-8"
        )
        (stubs_dir / "systemd_units.json").write_text(
            json.dumps(INIT_SYSTEM["gunnchos_units"], indent=2) + "\n", encoding="utf-8"
        )

        blueprint_bytes = _canonical_json(blueprint)
        content_digest = _sha256_bytes(blueprint_bytes)

        sbom = self.sbom()
        factory = self.factory_image_stub(content_digest)
        manifest = self.version_manifest(content_digest)

        artifacts = {
            "blueprint.json": blueprint,
            "version_manifest.json": manifest,
            "sbom.cdx.json": sbom,
            "dev_factory_image.json": factory,
            "sandbox_hook.json": SANDBOX_HOOK,
            "updater_hook.json": UPDATER_HOOK,
            "recovery_hook.json": RECOVERY_HOOK,
        }

        hashes: dict[str, str] = {}
        for name, payload in artifacts.items():
            path = root / name
            data = _canonical_json(payload)
            path.write_bytes(data + b"\n")
            hashes[name] = _sha256_bytes(data)

        provenance = self.provenance(hashes)
        prov_path = root / "provenance.json"
        prov_bytes = _canonical_json(provenance)
        prov_path.write_bytes(prov_bytes + b"\n")
        hashes["provenance.json"] = _sha256_bytes(prov_bytes)

        # DEV signature over content digest — rejects production key material by construction
        signature = {
            "realm": "DEV",
            "alg": "HMAC-SHA256-DEV-STUB",
            "content_digest_sha256": content_digest,
            "signature": _dev_hmac(content_digest.encode("utf-8"), DEV_REALM_KEY_MATERIAL),
            "production_keys_used": False,
            "label": "DEV_SIGNED_NOT_PRODUCTION_FACTORY_IMAGE",
        }
        sig_path = root / "dev_signature.json"
        sig_bytes = _canonical_json(signature)
        sig_path.write_bytes(sig_bytes + b"\n")
        hashes["dev_signature.json"] = _sha256_bytes(sig_bytes)

        checksums = {"files": hashes, "content_digest_sha256": content_digest}
        (root / "CHECKSUMS.json").write_bytes(_canonical_json(checksums) + b"\n")

        return {
            "out_dir": str(root),
            "content_digest_sha256": content_digest,
            "hashes": hashes,
            "signature": signature,
            "bootable": False,
            "production_keys_used": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }


def validate_image_bundle(out_dir: str | Path) -> dict[str, Any]:
    root = Path(out_dir)
    required = [
        "blueprint.json",
        "version_manifest.json",
        "sbom.cdx.json",
        "dev_factory_image.json",
        "provenance.json",
        "dev_signature.json",
        "CHECKSUMS.json",
        "sandbox_hook.json",
        "updater_hook.json",
        "recovery_hook.json",
    ]
    checks: list[dict[str, Any]] = []
    missing = [name for name in required if not (root / name).exists()]
    checks.append({"check": "required_artifacts", "ok": not missing, "missing": missing})

    if missing:
        return {
            "ok": False,
            "token": None,
            "checks": checks,
            "status_tokens": [TOKEN_PHYSICAL_PENDING],
            "claim_boundary": CLAIM_BOUNDARY,
            "full_operational_product_claimed": False,
        }

    checksums = json.loads((root / "CHECKSUMS.json").read_text(encoding="utf-8"))
    hash_ok = True
    for name, expected in checksums["files"].items():
        # Recompute over canonical content (file may have trailing newline)
        raw = (root / name).read_bytes()
        # Files were written as canonical + newline
        body = raw[:-1] if raw.endswith(b"\n") else raw
        actual = _sha256_bytes(body)
        if actual != expected:
            hash_ok = False
            checks.append({"check": f"hash:{name}", "ok": False, "expected": expected, "actual": actual})
    checks.append({"check": "checksums_match", "ok": hash_ok})

    manifest = json.loads((root / "version_manifest.json").read_text(encoding="utf-8"))
    factory = json.loads((root / "dev_factory_image.json").read_text(encoding="utf-8"))
    signature = json.loads((root / "dev_signature.json").read_text(encoding="utf-8"))
    sbom = json.loads((root / "sbom.cdx.json").read_text(encoding="utf-8"))
    blueprint = json.loads((root / "blueprint.json").read_text(encoding="utf-8"))

    checks.append(
        {
            "check": "digest_consistency",
            "ok": (
                manifest["content_digest_sha256"]
                == factory["content_digest_sha256"]
                == signature["content_digest_sha256"]
                == checksums["content_digest_sha256"]
            ),
        }
    )
    checks.append(
        {
            "check": "no_production_keys",
            "ok": (
                manifest.get("production_keys_used") is False
                and factory.get("production_keys_used") is False
                and signature.get("production_keys_used") is False
            ),
        }
    )
    checks.append({"check": "not_bootable_claimed", "ok": manifest.get("bootable") is False})
    checks.append({"check": "dev_realm", "ok": signature.get("realm") == "DEV"})
    expected_sig = _dev_hmac(
        signature["content_digest_sha256"].encode("utf-8"), DEV_REALM_KEY_MATERIAL
    )
    checks.append({"check": "dev_signature_valid", "ok": signature.get("signature") == expected_sig})
    checks.append({"check": "sbom_has_components", "ok": len(sbom.get("components") or []) >= 3})
    for key in (
        "kernel",
        "bootloader",
        "init",
        "drivers",
        "filesystem",
        "compositor_shell",
        "packages",
        "sandbox",
        "updater",
        "recovery",
        "vm_emulation_target",
    ):
        checks.append({"check": f"blueprint_has_{key}", "ok": key in blueprint})

    # Reproducibility: rebuild in temp and compare digest
    with tempfile.TemporaryDirectory() as tmp:
        rebuild = ReproducibleImageBuilder(
            ImageBuildRequest(
                version=manifest["version"],
                channel=manifest["channel"],
                build_id=manifest["build_id"],
                sku=manifest["sku"],
                out_dir=tmp,
            )
        ).build()
        checks.append(
            {
                "check": "reproducible_digest",
                "ok": rebuild["content_digest_sha256"] == checksums["content_digest_sha256"],
            }
        )

    ok = all(c["ok"] for c in checks)
    tokens = [TOKEN_DIGITAL_PASS] if ok else []
    tokens.append(TOKEN_PHYSICAL_PENDING)
    return {
        "ok": ok,
        "token": TOKEN_DIGITAL_PASS if ok else None,
        "status_tokens": tokens,
        "checks": checks,
        "content_digest_sha256": checksums["content_digest_sha256"],
        "claim_boundary": CLAIM_BOUNDARY,
        "full_operational_product_claimed": False,
        "production_keys_used": False,
        "bootable": False,
    }


def build_and_validate(out_dir: str | Path | None = None) -> dict[str, Any]:
    builder = ReproducibleImageBuilder()
    if out_dir:
        builder.request.out_dir = str(out_dir)
    built = builder.build()
    validation = validate_image_bundle(built["out_dir"])
    return {"build": built, "validation": validation}
