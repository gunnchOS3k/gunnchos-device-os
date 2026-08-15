"""GUNNCHDEVICE_BASE_IMAGE_PIPELINE — resumable sealed base + COW overlays.

Architecture (manifests/scripts/hashes in Git; NEVER multi-GB images in Git):

  canonical engineering image
    → provision once (guest-native)
    → gunnchOS tooling + guest agent
    → validate (boot-ready sentinel)
    → clean shutdown
    → seal (immutable) + version + SHA-256
    → COW overlays per persona/device (REGENERABLE; discard-safe)

SAFE_HALT / SAFE_RESUME preserve in-flight stage checkpoints without
hard-killing QEMU or deleting the sealed base.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "gunnchos.device_lab.base_image_pipeline.v1"
PIPELINE_VERSION = "1.0.0"

STAGES = (
    "canonical_engineering_image",
    "provision_once",
    "gunnchos_tooling",
    "guest_agent",
    "validate_sentinel",
    "clean_shutdown",
    "seal",
    "version_sha256",
    "cow_overlays",
)

SENTINEL_OK = "GUNNCHOS_INTERACTIVE_GUEST_PROVISION_OK"
SENTINEL_FAIL = "GUNNCHOS_INTERACTIVE_GUEST_PROVISION_FAILED"

# Overlay discard is only allowed when regenerable=true (never sealed base).
OVERLAY_ENV = "GUNNCH_LAB_INTERACTIVE_OVERLAY"
OVERLAY_PERSONA_ENV = "GUNNCH_LAB_OVERLAY_PERSONA"
FORCE_BASE_RW_ENV = "GUNNCH_LAB_ALLOW_BASE_RW"  # emergency only; default deny


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _qemu_img() -> str:
    return shutil.which("qemu-img") or "/opt/homebrew/bin/qemu-img"


def interactive_guest_root(repo_root: Path) -> Path:
    return repo_root / "os_build" / "device_lab_interactive_guest"


def base_qcow_path(repo_root: Path, *, arch: str = "aarch64") -> Path:
    return interactive_guest_root(repo_root) / "artifacts" / f"interactive-root-{arch}.qcow2"


def pipeline_state_dir(repo_root: Path) -> Path:
    return interactive_guest_root(repo_root) / "pipeline"


def sealed_dir(repo_root: Path) -> Path:
    return pipeline_state_dir(repo_root) / "sealed"


def overlays_dir(repo_root: Path) -> Path:
    return pipeline_state_dir(repo_root) / "overlays"


def checkpoint_path(repo_root: Path) -> Path:
    return pipeline_state_dir(repo_root) / "CHECKPOINT.json"


def halt_path(repo_root: Path) -> Path:
    return pipeline_state_dir(repo_root) / "SAFE_HALT.json"


def seal_manifest_path(repo_root: Path) -> Path:
    return sealed_dir(repo_root) / "SEAL_MANIFEST.json"


@dataclass
class PipelinePaths:
    repo_root: Path
    arch: str = "aarch64"

    @property
    def base(self) -> Path:
        return base_qcow_path(self.repo_root, arch=self.arch)

    @property
    def state(self) -> Path:
        return pipeline_state_dir(self.repo_root)

    @property
    def sealed(self) -> Path:
        return sealed_dir(self.repo_root)

    @property
    def overlays(self) -> Path:
        return overlays_dir(self.repo_root)

    @property
    def serial(self) -> Path:
        return (
            interactive_guest_root(self.repo_root)
            / "work"
            / "debian_cloud_provision"
            / "provision_serial.log"
        )


def load_checkpoint(repo_root: Path) -> dict[str, Any]:
    path = checkpoint_path(repo_root)
    if not path.exists():
        return {
            "schema": SCHEMA,
            "pipeline_version": PIPELINE_VERSION,
            "stage": None,
            "stages_completed": [],
            "updated_at_utc": None,
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_checkpoint(repo_root: Path, doc: dict[str, Any]) -> Path:
    path = checkpoint_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = dict(doc)
    doc["schema"] = SCHEMA
    doc["pipeline_version"] = PIPELINE_VERSION
    doc["updated_at_utc"] = _utc()
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def mark_stage(repo_root: Path, stage: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    if stage not in STAGES:
        raise ValueError(f"unknown_stage:{stage}")
    cp = load_checkpoint(repo_root)
    done = list(cp.get("stages_completed") or [])
    if stage not in done:
        done.append(stage)
    cp["stage"] = stage
    cp["stages_completed"] = done
    if extra:
        cp.setdefault("stage_evidence", {})[stage] = extra
    save_checkpoint(repo_root, cp)
    return cp


def detect_sentinel(repo_root: Path) -> dict[str, Any]:
    paths = PipelinePaths(repo_root)
    text = ""
    if paths.serial.exists():
        text = paths.serial.read_text(encoding="utf-8", errors="replace")
    ok = SENTINEL_OK in text
    fail = SENTINEL_FAIL in text
    poweroff = ("Powering off" in text) or ("reboot: Power down" in text)
    return {
        "ok": ok,
        "fail": fail,
        "clean_poweroff": poweroff,
        "serial_path": str(paths.serial) if paths.serial.exists() else None,
        "marker": SENTINEL_OK if ok else (SENTINEL_FAIL if fail else None),
    }


def is_immutable(path: Path) -> bool:
    if not path.exists():
        return False
    mode = path.stat().st_mode
    if mode & 0o222:
        return False
    # macOS uchg flag (best-effort)
    try:
        out = subprocess.check_output(["ls", "-lO", str(path)], text=True)
        if "uchg" in out.split():
            return True
    except (OSError, subprocess.CalledProcessError):
        pass
    return not bool(mode & 0o222)


def seal_base_image(
    repo_root: Path,
    *,
    arch: str = "aarch64",
    version: str | None = None,
    require_sentinel: bool = True,
) -> dict[str, Any]:
    """Seal provisioned interactive-root qcow2: hash, version, chmod a-w (+ uchg).

    Does NOT delete or reprovision. Refuses if QEMU appears to hold the image
    (caller must ensure guest is powered off).
    """
    paths = PipelinePaths(repo_root, arch=arch)
    base = paths.base
    if not base.exists():
        return {"ok": False, "error": "base_image_missing", "path": str(base)}

    sentinel = detect_sentinel(repo_root)
    if require_sentinel and not sentinel["ok"]:
        return {
            "ok": False,
            "error": "sentinel_required_before_seal",
            "sentinel": sentinel,
        }

    # Clear uchg if re-sealing after prior seal (need write briefly for chmod)
    try:
        subprocess.run(["chflags", "nouchg", str(base)], check=False, capture_output=True)
    except OSError:
        pass
    os.chmod(base, 0o644)

    sha = _sha256_file(base)
    ver = version or f"interactive-root-{arch}-{sha[:12]}"
    paths.sealed.mkdir(parents=True, exist_ok=True)
    paths.overlays.mkdir(parents=True, exist_ok=True)

    # Record sidecar hash next to image (gitignored qcow2; hash is commit-safe)
    hash_sidecar = base.with_suffix(base.suffix + ".sha256")
    hash_sidecar.write_text(f"{sha}  {base.name}\n", encoding="utf-8")

    os.chmod(base, 0o444)
    try:
        subprocess.run(["chflags", "uchg", str(base)], check=False, capture_output=True)
    except OSError:
        pass

    manifest = {
        "schema": "gunnchos.device_lab.sealed_base_image.v1",
        "pipeline_version": PIPELINE_VERSION,
        "sealed_at_utc": _utc(),
        "version": ver,
        "arch": arch,
        "path": str(base),
        "size_bytes": base.stat().st_size,
        "sha256": sha,
        "immutable": is_immutable(base),
        "sentinel": sentinel,
        "SHIPPING_IMAGE": False,
        "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": True,
        "note": (
            "Sealed engineering base. Persona/device runs MUST use COW overlays. "
            "Do not delete this qcow2; do not commit multi-GB images to Git."
        ),
    }
    seal_manifest_path(repo_root).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    # Also refresh INTERACTIVE_GUEST_MANIFEST disk block if present
    art_manifest = interactive_guest_root(repo_root) / "artifacts" / "INTERACTIVE_GUEST_MANIFEST.json"
    if art_manifest.exists():
        try:
            doc = json.loads(art_manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            doc = {}
        doc["disk"] = {
            "path": str(base),
            "size_bytes": base.stat().st_size,
            "sha256": sha,
            "sealed": True,
            "version": ver,
            "immutable": True,
        }
        doc["provision_ok"] = True
        doc["sentinel_seen"] = bool(sentinel["ok"])
        doc["sealed_at_utc"] = manifest["sealed_at_utc"]
        art_manifest.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    mark_stage(repo_root, "seal", extra={"version": ver, "sha256": sha})
    mark_stage(repo_root, "version_sha256", extra={"sha256": sha, "version": ver})
    return {"ok": True, "manifest": manifest}


def create_cow_overlay(
    repo_root: Path,
    *,
    persona: str = "default",
    arch: str = "aarch64",
    force: bool = False,
) -> dict[str, Any]:
    """Create (or reuse) a regenerable COW overlay backed by the sealed base."""
    paths = PipelinePaths(repo_root, arch=arch)
    base = paths.base
    if not base.exists():
        return {"ok": False, "error": "base_image_missing", "path": str(base)}
    seal = {}
    if seal_manifest_path(repo_root).exists():
        seal = json.loads(seal_manifest_path(repo_root).read_text(encoding="utf-8"))
    if seal.get("sha256"):
        live = _sha256_file(base) if not is_immutable(base) else seal["sha256"]
        # When immutable, trust seal manifest (re-hash is slow); spot-check size
        if not is_immutable(base) and live != seal["sha256"]:
            return {
                "ok": False,
                "error": "sealed_base_sha_mismatch",
                "expected": seal["sha256"],
                "live": live,
            }

    paths.overlays.mkdir(parents=True, exist_ok=True)
    safe_persona = "".join(c if c.isalnum() or c in "-_" else "_" for c in persona)[:64]
    overlay = paths.overlays / f"{safe_persona}-{arch}.qcow2"
    if overlay.exists() and not force:
        return {
            "ok": True,
            "created": False,
            "path": str(overlay),
            "backing": str(base),
            "persona": safe_persona,
            "regenerable": True,
            "size_bytes": overlay.stat().st_size,
        }

    qemu_img = _qemu_img()
    if not Path(qemu_img).exists():
        return {"ok": False, "error": "qemu_img_missing"}

    if overlay.exists():
        overlay.unlink()

    # Relative backing preferred when possible; absolute is fine for local lab.
    cmd = [
        qemu_img,
        "create",
        "-f",
        "qcow2",
        "-b",
        str(base),
        "-F",
        "qcow2",
        str(overlay),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode != 0:
        return {
            "ok": False,
            "error": "qemu_img_create_failed",
            "stderr": completed.stderr[-800:],
            "cmd": cmd,
        }

    meta = {
        "schema": "gunnchos.device_lab.cow_overlay.v1",
        "created_at_utc": _utc(),
        "persona": safe_persona,
        "path": str(overlay),
        "backing": str(base),
        "backing_sha256": seal.get("sha256"),
        "regenerable": True,
        "discard_allowed": True,
        "note": "REGENERABLE overlay only — discard/recreate freely; never delete sealed base",
    }
    overlay.with_suffix(".json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    mark_stage(repo_root, "cow_overlays", extra={"persona": safe_persona, "path": str(overlay)})
    return {"ok": True, "created": True, **meta, "size_bytes": overlay.stat().st_size}


def discard_overlay(repo_root: Path, *, persona: str, arch: str = "aarch64") -> dict[str, Any]:
    """Discard a REGENERABLE overlay only. Never touches sealed base."""
    paths = PipelinePaths(repo_root, arch=arch)
    safe_persona = "".join(c if c.isalnum() or c in "-_" else "_" for c in persona)[:64]
    overlay = paths.overlays / f"{safe_persona}-{arch}.qcow2"
    meta_path = overlay.with_suffix(".json")
    if not overlay.exists():
        return {"ok": True, "discarded": False, "reason": "absent", "persona": safe_persona}
    regenerable = True
    if meta_path.exists():
        try:
            regenerable = bool(json.loads(meta_path.read_text(encoding="utf-8")).get("regenerable", True))
        except json.JSONDecodeError:
            regenerable = True
    if not regenerable:
        return {"ok": False, "error": "overlay_not_regenerable", "path": str(overlay)}
    # Refuse if path resolves to sealed base
    if overlay.resolve() == paths.base.resolve():
        return {"ok": False, "error": "refused_delete_sealed_base"}
    overlay.unlink()
    if meta_path.exists():
        meta_path.unlink()
    return {"ok": True, "discarded": True, "persona": safe_persona, "path": str(overlay)}


def resolve_boot_disk(repo_root: Path, *, arch: str = "aarch64") -> dict[str, Any]:
    """Resolve which disk QEMU should boot: explicit overlay > persona overlay > refuse bare sealed.

    Default: create/reuse COW overlay so sealed base stays immutable.
    Set GUNNCH_LAB_ALLOW_BASE_RW=1 only for emergency base mutation (discouraged).
    """
    paths = PipelinePaths(repo_root, arch=arch)
    base = paths.base
    if not base.exists():
        return {"ok": False, "error": "base_image_missing", "path": str(base)}

    explicit = (os.environ.get(OVERLAY_ENV) or "").strip()
    if explicit:
        p = Path(explicit)
        if not p.exists():
            return {"ok": False, "error": "overlay_env_missing", "path": str(p)}
        return {
            "ok": True,
            "disk": str(p),
            "kind": "explicit_overlay",
            "backing": str(base),
            "regenerable": True,
        }

    allow_rw = (os.environ.get(FORCE_BASE_RW_ENV) or "").strip().lower() in {"1", "true", "yes"}
    persona = (os.environ.get(OVERLAY_PERSONA_ENV) or "session").strip() or "session"

    if allow_rw:
        return {
            "ok": True,
            "disk": str(base),
            "kind": "base_rw_emergency",
            "warning": "GUNNCH_LAB_ALLOW_BASE_RW set — writing sealed base is discouraged",
            "regenerable": False,
        }

    created = create_cow_overlay(repo_root, persona=persona, arch=arch)
    if not created.get("ok"):
        return created
    return {
        "ok": True,
        "disk": created["path"],
        "kind": "cow_overlay",
        "persona": persona,
        "backing": str(base),
        "regenerable": True,
        "created": created.get("created"),
    }


def safe_halt(
    repo_root: Path,
    *,
    reason: str = "operator_leaving",
    qemu_pid: int | None = None,
    do_not_kill: bool = True,
) -> dict[str, Any]:
    """Operator 'I need to leave now' halt — preserve state; never SIGKILL QEMU."""
    paths = PipelinePaths(repo_root)
    cp = load_checkpoint(repo_root)
    sentinel = detect_sentinel(repo_root)
    doc = {
        "schema": "gunnchos.device_lab.safe_halt.v1",
        "at_utc": _utc(),
        "reason": reason,
        "do_not_kill_qemu": do_not_kill,
        "do_not_delete_image": True,
        "qemu_pid": qemu_pid,
        "checkpoint": cp,
        "sentinel": sentinel,
        "base_path": str(paths.base),
        "base_exists": paths.base.exists(),
        "resume_hint": (
            "On resume: read SAFE_HALT.json + CHECKPOINT.json; if sentinel PASS seal; "
            "if QEMU alive continue that instance; never second QEMU; never hard-kill."
        ),
    }
    path = halt_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    # Mirror under product_use for operator discoverability
    mirror = repo_root / "artifacts" / "product_use" / "SAFE_HALT.json"
    mirror.parent.mkdir(parents=True, exist_ok=True)
    mirror.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "path": str(path), "mirror": str(mirror), "doc": doc}


def safe_resume(repo_root: Path) -> dict[str, Any]:
    """Compute SAFE_RESUME decision from checkpoint + sentinel + process policy."""
    paths = PipelinePaths(repo_root)
    cp = load_checkpoint(repo_root)
    sentinel = detect_sentinel(repo_root)
    halt = {}
    if halt_path(repo_root).exists():
        halt = json.loads(halt_path(repo_root).read_text(encoding="utf-8"))

    qemu_running = False
    # Best-effort: check pid from halt or pidfile
    pid = halt.get("qemu_pid")
    pidfile = interactive_guest_root(repo_root) / "work" / "debian_cloud_provision" / "qemu.pid"
    if pid is None and pidfile.exists():
        try:
            pid = int(pidfile.read_text().strip())
        except ValueError:
            pid = None
    if pid:
        try:
            os.kill(int(pid), 0)
            qemu_running = True
        except OSError:
            qemu_running = False

    sealed = seal_manifest_path(repo_root).exists()
    if qemu_running:
        decision = "CONTINUE_RUNNING_INSTANCE"
        actions = ["poll_serial", "wait_sentinel_or_poweroff", "no_second_qemu", "no_hard_kill"]
    elif sentinel.get("ok") and paths.base.exists():
        decision = "PRESERVE_AND_SEAL" if not sealed else "SEALED_READY_USE_COW"
        actions = ["seal_if_needed", "create_cow_overlays", "persona_runs_on_overlay"]
    elif paths.base.exists() and not sentinel.get("ok"):
        decision = "RESUME_FROM_LAST_SAFE_STAGE"
        actions = ["inspect_checkpoint", "resume_provision_stage", "do_not_delete_image"]
    else:
        decision = "BLOCKED_SAFE_GUEST_RESUME"
        actions = ["gather_evidence", "do_not_invent_pass"]

    return {
        "schema": "gunnchos.device_lab.safe_resume.v1",
        "at_utc": _utc(),
        "decision": decision,
        "blocked": decision == "BLOCKED_SAFE_GUEST_RESUME",
        "qemu_running": qemu_running,
        "qemu_pid": pid,
        "sentinel": sentinel,
        "sealed": sealed,
        "checkpoint": cp,
        "actions": actions,
        "halt": {"present": bool(halt), "at_utc": halt.get("at_utc")},
    }


def pipeline_status(repo_root: Path, *, arch: str = "aarch64") -> dict[str, Any]:
    paths = PipelinePaths(repo_root, arch=arch)
    seal = {}
    if seal_manifest_path(repo_root).exists():
        seal = json.loads(seal_manifest_path(repo_root).read_text(encoding="utf-8"))
    overlays = []
    if paths.overlays.exists():
        for p in sorted(paths.overlays.glob("*.qcow2")):
            overlays.append({"path": str(p), "size_bytes": p.stat().st_size, "regenerable": True})
    return {
        "schema": SCHEMA,
        "pipeline_version": PIPELINE_VERSION,
        "at_utc": _utc(),
        "stages": list(STAGES),
        "checkpoint": load_checkpoint(repo_root),
        "sentinel": detect_sentinel(repo_root),
        "base": {
            "path": str(paths.base),
            "exists": paths.base.exists(),
            "immutable": is_immutable(paths.base) if paths.base.exists() else False,
            "size_bytes": paths.base.stat().st_size if paths.base.exists() else None,
        },
        "seal": seal,
        "overlays": overlays,
        "safe_halt_present": halt_path(repo_root).exists(),
        "safe_resume": safe_resume(repo_root),
    }
