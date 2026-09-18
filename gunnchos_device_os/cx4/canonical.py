"""Canonical CX guest overlay provenance + fail-closed backing-chain repair.

Preferred outcome:
- durable CX base independent of ephemeral worktrees
- regenerable campaign overlay per wave
- qemu-img backing-chain validation before boot
- no destructive mutation of historical evidence images
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from gunnchos_device_os.cx2g.qemu import host_prereqs
from gunnchos_device_os.cx4.paths import (
    CX2H2_OVERLAY_NAME,
    CX2H3_OVERLAY_NAME,
    CX2H4_OVERLAY_NAME,
    CX4_OVERLAY_NAME,
    canonical_root,
    durable_device_os_root,
    ensure_canonical_tree,
    ensure_lab_tree,
    evidence_root,
    repo_root_from_here,
)


def _real_file(path: Path) -> bool:
    try:
        return path.is_file() and not path.is_symlink() or (path.is_symlink() and path.resolve().is_file())
    except OSError:
        return False


def _is_usable_qcow(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        target = path.resolve(strict=True)
    except Exception:
        return False
    return target.is_file() and target.stat().st_size > 1024


def find_durable_cx2h2(repo: Optional[Path] = None) -> Optional[Path]:
    repo = repo or repo_root_from_here()
    durable = durable_device_os_root(repo)
    candidates = [
        durable / "os_build" / "cx2h2_linux_lab" / "overlays" / CX2H2_OVERLAY_NAME,
        repo / "os_build" / "cx2h2_linux_lab" / "overlays" / CX2H2_OVERLAY_NAME,
        Path(os.environ["GUNNCHOS_CX2H2_OVERLAY"]) if os.environ.get("GUNNCHOS_CX2H2_OVERLAY") else None,
    ]
    # Sibling worktree leftovers (may be symlinks into durable)
    wt_root = durable / ".worktrees"
    if wt_root.is_dir():
        for child in sorted(wt_root.iterdir()):
            candidates.append(child / "os_build" / "cx2h2_linux_lab" / "overlays" / CX2H2_OVERLAY_NAME)
    for c in candidates:
        if c and _is_usable_qcow(c):
            return c.resolve()
    return None


def validate_backing_chain(image: Path, *, qimg: Optional[str] = None) -> Dict[str, Any]:
    qimg = qimg or host_prereqs().get("qemu_img")
    result: Dict[str, Any] = {
        "ok": False,
        "image": str(image),
        "layers": [],
        "blocker": None,
    }
    if not qimg:
        result["blocker"] = "CX4_QEMU_IMG_MISSING"
        return result
    if not _is_usable_qcow(image):
        result["blocker"] = "CX4_OVERLAY_MISSING"
        return result
    try:
        proc = subprocess.run(
            [qimg, "info", "--backing-chain", "--output=json", str(image)],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        result["blocker"] = f"CX4_QEMU_IMG_EXEC_FAILED:{exc}"
        return result
    if proc.returncode != 0:
        result["blocker"] = "CX4_BACKING_CHAIN_BROKEN"
        result["stderr"] = (proc.stderr or "")[-800:]
        return result
    try:
        data = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        result["blocker"] = "CX4_BACKING_CHAIN_PARSE_FAILED"
        result["stdout"] = (proc.stdout or "")[:500]
        return result
    if isinstance(data, dict):
        layers = [data]
        cur = data
        # older qemu may nest differently; also accept list
        while True:
            bf = cur.get("full-backing-filename") or cur.get("backing-filename")
            if not bf:
                break
            # already flattened by --backing-chain list form preferred
            break
    elif isinstance(data, list):
        layers = data
    else:
        result["blocker"] = "CX4_BACKING_CHAIN_UNEXPECTED"
        return result

    # Prefer list form; if single dict, re-run text parse for filenames
    if isinstance(data, dict):
        text = subprocess.run(
            [qimg, "info", "--backing-chain", str(image)],
            capture_output=True,
            text=True,
            check=False,
        )
        layers_out: List[Dict[str, Any]] = []
        current: Dict[str, Any] = {}
        for line in (text.stdout or "").splitlines():
            if line.startswith("image:"):
                if current:
                    layers_out.append(current)
                current = {"filename": line.split(":", 1)[1].strip()}
            elif line.startswith("backing file:"):
                current["backing_file"] = line.split(":", 1)[1].strip()
        if current:
            layers_out.append(current)
        layers = layers_out
    else:
        layers_out = []
        for item in layers:
            layers_out.append(
                {
                    "filename": item.get("filename") or item.get("file", {}).get("filename"),
                    "backing_file": item.get("full-backing-filename") or item.get("backing-filename"),
                    "virtual_size": item.get("virtual-size"),
                    "actual_size": item.get("actual-size"),
                }
            )
        layers = layers_out

    result["layers"] = layers
    for layer in layers:
        fn = layer.get("filename")
        if fn and not Path(fn).is_file():
            result["blocker"] = "CX4_BACKING_CHAIN_BROKEN"
            result["missing"] = fn
            return result
        bf = layer.get("backing_file")
        if bf and not Path(bf).is_file():
            result["blocker"] = "CX4_BACKING_CHAIN_BROKEN"
            result["missing"] = bf
            return result
    result["ok"] = bool(layers)
    if not result["ok"]:
        result["blocker"] = "CX4_BACKING_CHAIN_EMPTY"
    return result


def _create_child_overlay(qimg: str, child: Path, parent: Path) -> Dict[str, Any]:
    child.parent.mkdir(parents=True, exist_ok=True)
    if child.exists() or child.is_symlink():
        # Never mutate historical images; replace only regenerable local children.
        try:
            child.unlink()
        except OSError as exc:
            return {"ok": False, "blocker": f"CX4_OVERLAY_UNLINK_FAILED:{exc}", "path": str(child)}
    try:
        os.chmod(parent, 0o444)
    except OSError:
        pass
    cmd = [qimg, "create", "-f", "qcow2", "-b", str(parent.resolve()), "-F", "qcow2", str(child)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "ok": proc.returncode == 0,
        "cmd": cmd,
        "returncode": proc.returncode,
        "stderr": (proc.stderr or "")[-500:],
        "path": str(child),
        "parent": str(parent),
    }


def _link_or_copy(src: Path, dst: Path) -> Dict[str, Any]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        if _is_usable_qcow(dst) and dst.resolve() == src.resolve():
            return {"ok": True, "reused": True, "path": str(dst), "mode": "existing"}
        try:
            dst.unlink()
        except OSError as exc:
            return {"ok": False, "blocker": f"CX4_CANONICAL_UNLINK_FAILED:{exc}"}
    # Prefer hardlink (same FS), then symlink, then copy.
    try:
        os.link(src, dst)
        return {"ok": True, "path": str(dst), "mode": "hardlink", "src": str(src)}
    except OSError:
        pass
    try:
        dst.symlink_to(src)
        return {"ok": True, "path": str(dst), "mode": "symlink", "src": str(src)}
    except OSError:
        pass
    try:
        shutil.copy2(src, dst)
        return {"ok": True, "path": str(dst), "mode": "copy", "src": str(src)}
    except OSError as exc:
        return {"ok": False, "blocker": f"CX4_CANONICAL_PROMOTE_FAILED:{exc}"}


def ensure_canonical_chain(repo: Optional[Path] = None, *, force_rebuild_missing: bool = True) -> Dict[str, Any]:
    """Promote durable CX2H2 and rebuild missing CX2H3/CX2H4 immutable layers."""
    repo = repo or repo_root_from_here()
    root = ensure_canonical_tree(repo)
    qimg = host_prereqs().get("qemu_img")
    out: Dict[str, Any] = {
        "schema": "gunnchos.cx4.guest_overlay_provenance.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ok": False,
        "canonical_root": str(root),
        "diagnosis": {},
        "actions": [],
        "blocker": None,
    }
    if not qimg:
        out["blocker"] = "CX4_QEMU_IMG_MISSING"
        return out

    durable_h2 = find_durable_cx2h2(repo)
    out["diagnosis"]["durable_cx2h2"] = str(durable_h2) if durable_h2 else None
    out["diagnosis"]["worktree_relative_parents_stale"] = True
    out["diagnosis"]["prior_cx2h3_cx2h4_status"] = "missing_or_broken_symlink"
    if not durable_h2:
        out["blocker"] = "CX4_DURABLE_CX2H2_MISSING"
        return out

    imm = root / "immutable"
    h2 = imm / CX2H2_OVERLAY_NAME
    h3 = imm / CX2H3_OVERLAY_NAME
    h4 = imm / CX2H4_OVERLAY_NAME

    promote = _link_or_copy(durable_h2, h2)
    out["actions"].append({"promote_cx2h2": promote})
    if not promote.get("ok"):
        out["blocker"] = promote.get("blocker") or "CX4_CX2H2_PROMOTE_FAILED"
        return out

    # Rebuild regenerable intermediate layers if missing/broken (additive; do not rewrite durable h2).
    for child, parent, label in (
        (h3, h2, "cx2h3"),
        (h4, h3, "cx2h4"),
    ):
        if _is_usable_qcow(child):
            chain = validate_backing_chain(child, qimg=qimg)
            if chain.get("ok"):
                out["actions"].append({f"reuse_{label}": {"ok": True, "path": str(child)}})
                continue
            if not force_rebuild_missing:
                out["blocker"] = chain.get("blocker") or f"CX4_{label.upper()}_CHAIN_BROKEN"
                out["actions"].append({f"validate_{label}": chain})
                return out
            # regenerate child only
        created = _create_child_overlay(qimg, child, parent)
        out["actions"].append({f"create_{label}": created})
        if not created.get("ok"):
            out["blocker"] = created.get("blocker") or f"CX4_{label.upper()}_CREATE_FAILED"
            return out

    for label, path in (("cx2h2", h2), ("cx2h3", h3), ("cx2h4", h4)):
        chain = validate_backing_chain(path, qimg=qimg)
        out["actions"].append({f"validate_{label}": {"ok": chain.get("ok"), "blocker": chain.get("blocker"), "layers": len(chain.get("layers") or [])}})
        if not chain.get("ok"):
            out["blocker"] = chain.get("blocker") or f"CX4_{label.upper()}_INVALID"
            out["chain"] = chain
            return out

    out["ok"] = True
    out["immutable"] = {
        "cx2h2": str(h2.resolve()),
        "cx2h3": str(h3.resolve()),
        "cx2h4": str(h4.resolve()),
    }
    out["note"] = (
        "CX2H3/CX2H4 content deltas lost with deleted worktree overlays; "
        "layers rebuilt as thin COW on durable CX2H2 for current-tip boot continuity."
    )
    return out


def prepare_campaign_overlay(repo: Optional[Path] = None, *, force: bool = False) -> Dict[str, Any]:
    """Create/reuse CX4 campaign overlay backed by canonical CX2H4."""
    repo = repo or repo_root_from_here()
    lab = ensure_lab_tree(repo)
    qimg = host_prereqs().get("qemu_img")
    result: Dict[str, Any] = {
        "ok": False,
        "overlay": str(lab / "overlays" / CX4_OVERLAY_NAME),
        "blocker": None,
    }
    canon = ensure_canonical_chain(repo)
    result["canonical"] = {
        "ok": canon.get("ok"),
        "blocker": canon.get("blocker"),
        "immutable": canon.get("immutable"),
        "canonical_root": canon.get("canonical_root"),
        "note": canon.get("note"),
    }
    if not canon.get("ok"):
        result["blocker"] = canon.get("blocker") or "CX4_CANONICAL_CHAIN_FAILED"
        return result
    if not qimg:
        result["blocker"] = "CX4_QEMU_IMG_MISSING"
        return result

    parent = Path(canon["immutable"]["cx2h4"])
    overlay = lab / "overlays" / CX4_OVERLAY_NAME
    result["parent"] = str(parent)

    if overlay.is_file() and not force:
        chain = validate_backing_chain(overlay, qimg=qimg)
        result["chain"] = chain
        if chain.get("ok"):
            result["ok"] = True
            result["reused"] = True
            return result
        # Broken campaign overlay — regenerate
        try:
            overlay.unlink()
        except OSError as exc:
            result["blocker"] = f"CX4_OVERLAY_UNLINK_FAILED:{exc}"
            return result

    created = _create_child_overlay(qimg, overlay, parent)
    result["create"] = created
    if not created.get("ok"):
        result["blocker"] = "CX4_OVERLAY_CREATE_FAILED"
        return result
    chain = validate_backing_chain(overlay, qimg=qimg)
    result["chain"] = chain
    if not chain.get("ok"):
        result["blocker"] = chain.get("blocker") or "CX4_BACKING_CHAIN_BROKEN"
        return result
    result["ok"] = True
    result["overlay"] = str(overlay)
    return result


def write_provenance(repo: Optional[Path] = None, overlay_info: Optional[Dict[str, Any]] = None) -> Path:
    repo = repo or repo_root_from_here()
    ev = evidence_root(repo)
    ev.mkdir(parents=True, exist_ok=True)
    payload = overlay_info or prepare_campaign_overlay(repo)
    path = ev / "CX4_GUEST_OVERLAY_PROVENANCE.json"
    path.write_text(json.dumps(payload, indent=2) + "\n")
    # Also mirror under canonical provenance
    ensure_canonical_tree(repo)
    (canonical_root(repo) / "provenance" / "CX4_GUEST_OVERLAY_PROVENANCE.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    return path
