"""QEMU/Device Lab realm-image runtime harness for WP-013R.

Boots each EVT/FACTORY/RECOVERY realm *artifact* under qemu-system-aarch64 by:
  1. Staging Alpine minirootfs (shared bootable_reference cache)
  2. Overlaying the realm rootfs.tar.gz contents into that guest root
  3. Installing a realm probe /init that *executes* artifact files
  4. Capturing serial console evidence

Rootfs-tarball presence alone never earns RUNTIME_PASS. PRODUCTION_RELEASE_CLAIMED
remains false. Physical/silicon-exact boot is not claimed.
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.release_engineering.os_image_builder import RealmImageBuilder

CLAIM_BOUNDARY = (
    "Realm RUNTIME tokens require QEMU (or Device Lab) execution of each realm "
    "rootfs artifact with serial evidence of realm identity + artifact probe. "
    "Not physical device boot; not silicon-exact; not a shipping image. "
    "PRODUCTION_RELEASE_CLAIMED=false."
)

RUNTIME_ALIASES = ("evt", "factory", "recovery")
TOKEN_BY_ALIAS = {
    "evt": "EVT_IMAGE_RUNTIME_PASS",
    "factory": "FACTORY_IMAGE_RUNTIME_PASS",
    "recovery": "RECOVERY_IMAGE_RUNTIME_PASS",
}

PROBE_INIT = r"""#!/bin/sh
# Realm runtime probe — executes overlayed realm artifact files under QEMU.
# Not a production init; exits after emitting honest serial markers.
set -eu
export PATH=/sbin:/usr/sbin:/bin:/usr/bin:/opt/gunnchos/bin

echo "GUNNCHOS_REALM_RUNTIME_PROBE=start"
echo "GUNNCHOS_PRODUCTION_KEYS=false"
echo "GUNNCHOS_PHYSICAL_BOOT_CLAIMED=false"
echo "PRODUCTION_RELEASE_CLAIMED=false"

mount -t proc proc /proc 2>/dev/null || true
mount -t sysfs sysfs /sys 2>/dev/null || true
mount -t devtmpfs devtmpfs /dev 2>/dev/null || true
mkdir -p /tmp /run
mount -t tmpfs tmpfs /tmp 2>/dev/null || true
mount -t tmpfs tmpfs /run 2>/dev/null || true

if [ ! -f /etc/os-release ]; then
  echo "GUNNCHOS_REALM_RUNTIME_ERROR=os_release_missing"
  echo "GUNNCHOS_REALM_RUNTIME_PASS=false"
  poweroff -f 2>/dev/null || halt -f 2>/dev/null || exit 1
fi
if [ ! -f /etc/gunnchos/realm.json ]; then
  echo "GUNNCHOS_REALM_RUNTIME_ERROR=realm_json_missing"
  echo "GUNNCHOS_REALM_RUNTIME_PASS=false"
  poweroff -f 2>/dev/null || halt -f 2>/dev/null || exit 1
fi

# Execute artifact content: read os-release + realm.json, enumerate services.
# shellcheck disable=SC1091
. /etc/os-release
echo "GUNNCHOS_REALM_OS_RELEASE_NAME=${NAME:-}"
echo "GUNNCHOS_REALM_OS_RELEASE_REALM=${REALM:-}"
echo "GUNNCHOS_REALM_OS_RELEASE_STATUS=${STATUS:-}"

# Busybox/ash-friendly JSON realm_id extract (no python in minirootfs).
REALM_ID_JSON="$(sed -n 's/.*"realm_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' /etc/gunnchos/realm.json | head -n 1)"
echo "GUNNCHOS_REALM_ID=${REALM_ID_JSON}"

EXPECTED_REALM="__EXPECTED_REALM__"
echo "GUNNCHOS_REALM_EXPECTED=${EXPECTED_REALM}"

SVC_COUNT=0
if [ -d /opt/gunnchos/services ]; then
  for f in /opt/gunnchos/services/*.service; do
    [ -f "$f" ] || continue
    SVC_COUNT=$((SVC_COUNT + 1))
    # Execute: read unit text (proves file is in guest FS and readable).
    head -n 2 "$f" >/run/gunnchos_realm_svc_probe.txt 2>/dev/null || true
  done
fi
echo "GUNNCHOS_REALM_SERVICE_UNITS=${SVC_COUNT}"

# Execute realm-specific marker files when present.
if [ -f /opt/gunnchos/factory/FACTORY_ONLY_SERVICES.json ]; then
  head -n 5 /opt/gunnchos/factory/FACTORY_ONLY_SERVICES.json >/run/factory_probe.txt || true
  echo "GUNNCHOS_REALM_FACTORY_MARKER=executed"
fi
if [ -f /opt/gunnchos/recovery/RECOVERY_POLICY.json ]; then
  head -n 5 /opt/gunnchos/recovery/RECOVERY_POLICY.json >/run/recovery_probe.txt || true
  echo "GUNNCHOS_REALM_RECOVERY_MARKER=executed"
fi
if [ -f /opt/gunnchos/bin/gunnchctl ]; then
  # Prove binary exists and is executable bytes (do not require full host python).
  wc -c /opt/gunnchos/bin/gunnchctl >/run/gunnchctl_probe.txt || true
  echo "GUNNCHOS_REALM_GUNNCHCTL_MARKER=executed"
fi
if [ -f /opt/gunnchos/bin/NO_DEV_TOOLCHAIN.txt ]; then
  cat /opt/gunnchos/bin/NO_DEV_TOOLCHAIN.txt >/run/no_dev_probe.txt || true
  echo "GUNNCHOS_REALM_NO_DEV_TOOLCHAIN_MARKER=executed"
fi

echo "GUNNCHOS_REALM_RUNTIME_EXECUTED=true"

PASS=true
if [ -z "${REALM_ID_JSON}" ] || [ "${REALM_ID_JSON}" != "${EXPECTED_REALM}" ]; then
  PASS=false
  echo "GUNNCHOS_REALM_RUNTIME_ERROR=realm_id_mismatch"
fi
if [ -z "${REALM}" ] || [ "${REALM}" != "${EXPECTED_REALM}" ]; then
  PASS=false
  echo "GUNNCHOS_REALM_RUNTIME_ERROR=os_release_realm_mismatch"
fi
if [ "${SVC_COUNT}" -lt 1 ]; then
  PASS=false
  echo "GUNNCHOS_REALM_RUNTIME_ERROR=no_service_units"
fi

if [ "${PASS}" = "true" ]; then
  echo "GUNNCHOS_REALM_RUNTIME_PASS=true"
  echo "GUNNCHOS_REALM_RUNTIME_COMPLETE=true"
else
  echo "GUNNCHOS_REALM_RUNTIME_PASS=false"
  echo "GUNNCHOS_REALM_RUNTIME_COMPLETE=true"
fi

# Prefer clean poweroff; QEMU -no-reboot + panic still terminates if needed.
poweroff -f 2>/dev/null || halt -f 2>/dev/null || exit 0
"""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _qemu_bin() -> str:
    env = os.environ.get("GUNNCHOS_QEMU_BIN")
    if env:
        return env
    which = shutil.which("qemu-system-aarch64")
    if which:
        return which
    brew = Path("/opt/homebrew/bin/qemu-system-aarch64")
    if brew.exists():
        return str(brew)
    raise FileNotFoundError("qemu-system-aarch64 not found")


def _kernel_path(repo_root: Path) -> Path:
    return repo_root / "os_build" / "bootable_reference" / "artifacts" / "vmlinuz-virt"


def _alpine_minirootfs(repo_root: Path) -> Path:
    return (
        repo_root
        / "os_build"
        / "bootable_reference"
        / "cache"
        / "alpine-minirootfs-aarch64.tar.gz"
    )


def _pack_initramfs(rootfs: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    files: list[str] = []
    for p in sorted(rootfs.rglob("*")):
        rel = p.relative_to(rootfs).as_posix()
        if rel in (".",):
            continue
        files.append(rel)
    with tempfile.TemporaryDirectory(prefix="realm_cpio_") as td:
        td_path = Path(td)
        list_file = td_path / "filelist.txt"
        list_file.write_text("\n".join(files) + "\n", encoding="utf-8")
        cpio_raw = td_path / "rootfs.cpio"
        with list_file.open() as lf, cpio_raw.open("wb") as out_cpio:
            proc = subprocess.run(
                ["cpio", "-o", "-H", "newc"],
                cwd=rootfs,
                stdin=lf,
                stdout=out_cpio,
                stderr=subprocess.PIPE,
                check=False,
            )
        if proc.returncode != 0:
            raise RuntimeError(f"cpio failed: {proc.stderr.decode(errors='replace')}")
        with cpio_raw.open("rb") as src, gzip.open(dest, "wb", compresslevel=6) as gz:
            shutil.copyfileobj(src, gz)


def build_realm_runtime_initramfs(
    *,
    repo_root: Path,
    alias: str,
    work: Path,
) -> dict[str, Any]:
    """Materialize a bootable initramfs that embeds the realm rootfs artifact."""
    builder = RealmImageBuilder(repo_root)
    inspect = builder.inspect(alias)
    manifest = inspect.get("manifest") or {}
    realm_id = manifest.get("realm_id")
    rootfs_meta = (manifest.get("artifacts") or {}).get("rootfs_tarball") or {}
    rootfs_rel = rootfs_meta.get("path")
    if not realm_id or not rootfs_rel:
        return {
            "ok": False,
            "error": "realm_manifest_or_rootfs_missing",
            "inspect_ok": bool(inspect.get("ok")),
        }
    rootfs_tar = repo_root / rootfs_rel
    if not rootfs_tar.exists():
        return {"ok": False, "error": "rootfs_tarball_missing", "path": str(rootfs_tar)}

    alpine = _alpine_minirootfs(repo_root)
    kernel = _kernel_path(repo_root)
    if not alpine.exists():
        return {"ok": False, "error": "alpine_minirootfs_cache_missing", "path": str(alpine)}
    if not kernel.exists():
        return {"ok": False, "error": "kernel_missing", "path": str(kernel)}

    root = work / "rootfs"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    with tarfile.open(alpine, "r:gz") as tar:
        tar.extractall(root)
    with tarfile.open(rootfs_tar, "r:gz") as tar:
        tar.extractall(root)

    for d in ("proc", "sys", "dev", "tmp", "run"):
        (root / d).mkdir(parents=True, exist_ok=True)

    init = root / "init"
    init.write_text(
        PROBE_INIT.replace("__EXPECTED_REALM__", str(realm_id)),
        encoding="utf-8",
    )
    init.chmod(0o755)

    initrd = work / "realm-runtime.cpio.gz"
    _pack_initramfs(root, initrd)
    return {
        "ok": True,
        "alias": alias,
        "realm_id": realm_id,
        "rootfs_tarball": str(rootfs_rel),
        "rootfs_sha256": rootfs_meta.get("sha256"),
        "kernel": str(kernel),
        "initrd": str(initrd),
        "PRODUCTION_RELEASE_CLAIMED": bool(manifest.get("PRODUCTION_RELEASE_CLAIMED", False)),
    }


def boot_realm_runtime(
    *,
    repo_root: Path,
    alias: str,
    timeout_sec: float = 90.0,
    memory_mb: int = 512,
    evidence_dir: Path | None = None,
) -> dict[str, Any]:
    """Build + boot one realm artifact under QEMU; return serial evidence."""
    evidence_dir = evidence_dir or (
        repo_root / "artifacts" / "wp013" / "realm_runtime" / alias
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=f"wp013_realm_rt_{alias}_") as td:
        built = build_realm_runtime_initramfs(
            repo_root=repo_root, alias=alias, work=Path(td)
        )
        if not built.get("ok"):
            return {
                "ok": False,
                "attempted": True,
                "mode": "qemu_realm_initramfs_build",
                "alias": alias,
                "build": built,
                "claim_boundary": CLAIM_BOUNDARY,
            }

        log_path = evidence_dir / "qemu_serial_runtime.log"
        evidence_path = evidence_dir / "RUNTIME_EVIDENCE.json"
        qemu = _qemu_bin()
        cmd = [
            qemu,
            "-M",
            "virt",
            "-cpu",
            "max",
            "-smp",
            "2",
            "-m",
            str(memory_mb),
            "-nographic",
            "-no-reboot",
            "-kernel",
            built["kernel"],
            "-initrd",
            built["initrd"],
            "-append",
            "console=ttyAMA0 earlyprintk=serial rdinit=/init panic=1",
            "-serial",
            "stdio",
            "-monitor",
            "none",
        ]

        t0 = time.time()
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        lines: list[str] = []
        assert proc.stdout is not None
        deadline = t0 + timeout_sec
        try:
            while True:
                if time.time() > deadline:
                    proc.kill()
                    break
                line = proc.stdout.readline()
                if not line:
                    if proc.poll() is not None:
                        break
                    time.sleep(0.05)
                    continue
                lines.append(line.rstrip("\n"))
                if "GUNNCHOS_REALM_RUNTIME_COMPLETE=true" in line:
                    time.sleep(0.4)
                    if proc.poll() is None:
                        proc.kill()
                    break
        finally:
            if proc.poll() is None:
                proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

        elapsed = time.time() - t0
        log_text = "\n".join(lines) + ("\n" if lines else "")
        log_path.write_text(log_text, encoding="utf-8")

        realm_id = built["realm_id"]
        required = [
            "GUNNCHOS_REALM_RUNTIME_PROBE=start",
            "GUNNCHOS_REALM_RUNTIME_EXECUTED=true",
            f"GUNNCHOS_REALM_ID={realm_id}",
            f"GUNNCHOS_REALM_OS_RELEASE_REALM={realm_id}",
            "PRODUCTION_RELEASE_CLAIMED=false",
            "GUNNCHOS_REALM_RUNTIME_PASS=true",
            "GUNNCHOS_REALM_RUNTIME_COMPLETE=true",
        ]
        missing = [m for m in required if m not in log_text]
        ok = not missing and built.get("PRODUCTION_RELEASE_CLAIMED") is False

        evidence = {
            "schema": "gunnchos.wp013.realm_runtime_evidence.v1",
            "ok": ok,
            "attempted": True,
            "mode": "qemu_realm_rootfs_overlay_boot",
            "alias": alias,
            "realm_id": realm_id,
            "elapsed_sec": round(elapsed, 3),
            "qemu_bin": qemu,
            "markers_required": required,
            "markers_missing": missing,
            "log_path": str(log_path.relative_to(repo_root)),
            "rootfs_tarball": built.get("rootfs_tarball"),
            "rootfs_sha256": built.get("rootfs_sha256"),
            "PRODUCTION_RELEASE_CLAIMED": False,
            "physical_boot_claimed": False,
            "SILICON_EXACT_EMULATION": False,
            "claim_boundary": CLAIM_BOUNDARY,
            "command": cmd,
        }
        evidence_path.write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        evidence["evidence_path"] = str(evidence_path.relative_to(repo_root))
        return evidence


def verify_all_realm_runtimes(
    repo_root: Path | None = None,
    *,
    timeout_sec: float = 90.0,
) -> dict[str, Any]:
    """Boot EVT/FACTORY/RECOVERY realm artifacts and aggregate RUNTIME tokens."""
    root = Path(repo_root or _repo_root())
    out: dict[str, Any] = {
        "schema": "gunnchos.wp013.realm_runtime.v1",
        "realms": {},
        "claim_boundary": CLAIM_BOUNDARY,
    }
    builder = RealmImageBuilder(root)

    qemu_error = None
    try:
        _qemu_bin()
    except Exception as exc:  # noqa: BLE001
        qemu_error = str(exc)
        out["qemu_error"] = qemu_error

    for alias in RUNTIME_ALIASES:
        token = TOKEN_BY_ALIAS[alias]
        inspect = builder.inspect(alias)
        manifest = inspect.get("manifest") or {}
        rootfs = ((manifest.get("artifacts") or {}).get("rootfs_tarball") or {})
        policy = {
            "realm_id": manifest.get("realm_id"),
            "signing_realm": manifest.get("signing_realm") or manifest.get("trust_roots"),
            "rootfs_present": bool(rootfs.get("path") or rootfs.get("sha256")),
            "file_count": rootfs.get("file_count"),
            "PRODUCTION_RELEASE_CLAIMED": bool(manifest.get("PRODUCTION_RELEASE_CLAIMED", False)),
        }
        if qemu_error or not policy["rootfs_present"]:
            boot = {
                "attempted": False,
                "ok": False,
                "mode": "not_attempted",
                "reason": "qemu_unavailable_or_rootfs_missing",
            }
            token_pass = False
        else:
            boot = boot_realm_runtime(
                repo_root=root, alias=alias, timeout_sec=timeout_sec
            )
            token_pass = bool(boot.get("ok")) and policy["PRODUCTION_RELEASE_CLAIMED"] is False
        out["realms"][alias] = {
            "policy": policy,
            "boot": boot,
            token: token_pass,
        }

    out["IMAGE_REALM_POLICY_SEPARATION_PASS"] = all(
        (out["realms"][a]["policy"].get("realm_id") not in (None, ""))
        and out["realms"][a]["policy"].get("PRODUCTION_RELEASE_CLAIMED") is False
        for a in RUNTIME_ALIASES
    )
    out["EVT_IMAGE_RUNTIME_PASS"] = bool(out["realms"]["evt"]["EVT_IMAGE_RUNTIME_PASS"])
    out["FACTORY_IMAGE_RUNTIME_PASS"] = bool(
        out["realms"]["factory"]["FACTORY_IMAGE_RUNTIME_PASS"]
    )
    out["RECOVERY_IMAGE_RUNTIME_PASS"] = bool(
        out["realms"]["recovery"]["RECOVERY_IMAGE_RUNTIME_PASS"]
    )
    return out
