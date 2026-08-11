"""WP-011R: attempt LIVE / DSXL / RING proofs against the provisioned
Interactive Development Guest — only ever writes a `*_PASS: true` token when
a live guest-agent session actually produced the evidence in this run.

Every attempt function returns its own honest result even when the guest
agent is unreachable, the compositor never came up, or a screenshot never
appeared — it never falls back to a stub answer and calls that a PASS.

DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST=true. SHIPPING_IMAGE=false.
SILICON_EXACT_EMULATION=false always.
"""
from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.profiles import load_profile
from gunnchos_device_os.device_lab.virtualization import guest_input
from gunnchos_device_os.device_lab.virtualization.dsxl_outputs import high_fidelity_dual_gate
from gunnchos_device_os.device_lab.virtualization.qemu_guest import start_qemu_guest

CLAIM = (
    "Interactive Development Guest proofs run against a real virtio-serial "
    "guest agent inside a Debian cloud-init-provisioned guest. "
    "SILICON_EXACT_EMULATION=false. DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST=true. "
    "SHIPPING_IMAGE=false. A *_PASS token here is only ever set true when this "
    "run's own agent responses (not a mailbox stub) demonstrate it."
)


def _evidence_dir(repo_root: Path, *sub: str) -> Path:
    d = repo_root / "artifacts" / "wp011r"
    for s in sub:
        d = d / s
    d.mkdir(parents=True, exist_ok=True)
    return d


def boot_interactive_guest(
    repo_root: Path,
    work: Path,
    *,
    dual: bool = False,
    boot_timeout_s: int = 180,
    memory_mb: int = 3072,
) -> dict[str, Any]:
    os.environ["GUNNCH_LAB_INTERACTIVE_GUEST"] = "1"
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    os.environ.setdefault("GUNNCHDEVICE_LAB_BOOT_TIMEOUT", str(boot_timeout_s))
    os.environ.setdefault("GUNNCHDEVICE_LAB_MEMORY_MB", str(memory_mb))
    if dual:
        os.environ["GUNNCHDEVICE_LAB_DUAL_GPU"] = "1"
    else:
        os.environ.pop("GUNNCHDEVICE_LAB_DUAL_GPU", None)
    profile = load_profile("dsxl_coder" if dual else "handheld_hybrid")
    result = start_qemu_guest(work=work, profile=profile, repo_root=repo_root, headless=True)
    return result


def _agent_call(session: Any, cmd: str, *, timeout_sec: float = 20.0, **kwargs: Any) -> dict[str, Any]:
    agent = getattr(session, "agent", None)
    if agent is None:
        return {"ok": False, "error": "no_agent_bound"}
    old_timeout = agent.timeout_sec
    agent.timeout_sec = timeout_sec
    try:
        return agent.call(cmd, **kwargs)
    finally:
        agent.timeout_sec = old_timeout


def _require_real_virtio_serial(resp: dict[str, Any]) -> bool:
    """Reject anything answered by the host mailbox stub — never a proof."""
    if not isinstance(resp, dict):
        return False
    transport = str(resp.get("transport") or "")
    label = str(resp.get("agent_path_label") or "")
    if "stub" in transport.lower() or "stub" in label.lower():
        return False
    return resp.get("ok") is not False or "reason" in resp  # allow honest ok:false diagnostics through


def attempt_live_visual_pass(session: Any, evidence_dir: Path) -> dict[str, Any]:
    import hashlib
    import socket as _socket

    result: dict[str, Any] = {"LIVE_GUNNCHOS_VISUAL_PASS": False, "claim_boundary": CLAIM}
    ping = _agent_call(session, "ping")
    result["ping"] = ping
    if not _require_real_virtio_serial(ping) or not ping.get("pong"):
        result["blocker"] = "guest_agent_not_reachable_over_real_virtio_serial"
        (evidence_dir / "LIVE_VISUAL_EVIDENCE.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result

    comp = _agent_call(session, "compositor_info")
    result["compositor_info"] = comp
    if not comp.get("available"):
        result["blocker"] = "compositor_not_available"
        (evidence_dir / "LIVE_VISUAL_EVIDENCE.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result

    launch = _agent_call(session, "app_launch", app="mousepad", timeout_sec=15.0)
    result["app_launch"] = launch
    time.sleep(2.0)

    before = _agent_call(session, "framebuffer_capture", timeout_sec=15.0)
    result["framebuffer_before"] = {k: v for k, v in before.items() if k != "bytes_b64"}
    before_bytes = base64.b64decode(before["bytes_b64"]) if before.get("bytes_b64") else b""

    host_before = evidence_dir / "host_fb_before.ppm"
    host_after = evidence_dir / "host_fb_after.ppm"
    host_cap: dict[str, Any] = {"ok": False, "RFB_HANDSHAKE_ALONE_ACCEPTED": False}
    mon = getattr(session, "monitor_sock", None)

    def _mon(cmd_line: str) -> None:
        s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        s.settimeout(8)
        s.connect(str(mon))
        try:
            s.recv(4096)
            s.sendall((cmd_line + "\n").encode())
            time.sleep(0.5)
            s.recv(8192)
        finally:
            s.close()

    if mon:
        try:
            _mon(f"screendump {host_before}")
            host_cap["before_exists"] = host_before.exists()
        except OSError as exc:
            host_cap["before_error"] = str(exc)

    inj = guest_input.inject_key(monitor_sock=getattr(session, "monitor_sock", None), key="a", agent=session.agent)
    result["input_injection"] = inj
    _agent_call(session, "input_inject", kind="text", text="gunnchOS live visual proof")
    time.sleep(1.0)

    after = _agent_call(session, "framebuffer_capture", timeout_sec=15.0)
    result["framebuffer_after"] = {k: v for k, v in after.items() if k != "bytes_b64"}
    after_bytes = base64.b64decode(after["bytes_b64"]) if after.get("bytes_b64") else b""

    if mon:
        try:
            _mon(f"screendump {host_after}")
            host_cap["after_exists"] = host_after.exists()
        except OSError as exc:
            host_cap["after_error"] = str(exc)

    if before_bytes:
        (evidence_dir / "shell_app_before.png").write_bytes(before_bytes)
    if after_bytes:
        (evidence_dir / "shell_app_after.png").write_bytes(after_bytes)

    def _ppm_nonblank(path: Path) -> tuple[bool, str]:
        if not path.exists():
            return False, ""
        data = path.read_bytes()
        if not data.startswith(b"P6") or len(data) < 64:
            return False, ""
        try:
            _, body = data.split(b"\n255\n", 1)
        except ValueError:
            return False, hashlib.sha256(data).hexdigest()
        ratio = (sum(1 for b in body if b != 0) / len(body)) if body else 0.0
        return ratio > 0.01, hashlib.sha256(data).hexdigest()

    host_nb_b, host_sha_b = _ppm_nonblank(host_before)
    host_nb_a, host_sha_a = _ppm_nonblank(host_after)
    host_cap.update(
        {
            "ok": bool(host_nb_b and host_nb_a),
            "before_nonblank": host_nb_b,
            "after_nonblank": host_nb_a,
            "before_sha256": host_sha_b,
            "after_sha256": host_sha_a,
            "changed": bool(host_sha_b and host_sha_a and host_sha_b != host_sha_a),
            "measurement_class": "HOST_OBSERVED",
            "note": "QEMU monitor screendump PPM — real virtio-gpu pixels, not RFB handshake alone",
        }
    )
    result["host_screendump"] = host_cap

    non_blank = len(before_bytes) > 2048 or len(after_bytes) > 2048 or bool(host_cap.get("ok"))
    changed = (
        (before_bytes != after_bytes if (before_bytes and after_bytes) else False)
        or bool(host_cap.get("changed"))
    )
    earned = bool(
        comp.get("available")
        and comp.get("compositor") == "weston"
        and launch.get("ok")
        and launch.get("alive_after_500ms")
        and non_blank
        and changed
    )
    result.update(
        {
            "LIVE_GUNNCHOS_VISUAL_PASS": earned,
            "non_blank_capture": non_blank,
            "diff_bytes": abs(len(after_bytes) - len(before_bytes)) if (before_bytes and after_bytes) else 0,
            "before_after_changed": changed,
            "note": (
                "Real weston + alive app + non-blank FB (guest and/or QEMU screendump) with input-visible delta"
                if earned
                else "Not earned — see compositor_info/app_launch/framebuffer_*/host_screendump"
            ),
        }
    )
    (evidence_dir / "LIVE_VISUAL_EVIDENCE.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def attempt_dsxl_dual_compositor_pass(session: Any, evidence_dir: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"DSXL_DUAL_COMPOSITOR_UX_PASS": False, "claim_boundary": CLAIM}
    disp = _agent_call(session, "display_info")
    result["display_info"] = disp
    gate = high_fidelity_dual_gate(disp.get("displays") or [], claim_guest_dual=True)
    result["dual_output_gate"] = gate

    comp = _agent_call(session, "compositor_info")
    result["compositor_info"] = comp
    outputs = int(comp.get("outputs") or 0)

    earned = bool(gate.get("GUEST_DUAL_OUTPUT_PASS") and comp.get("available") and outputs >= 2)
    result.update(
        {
            "DSXL_DUAL_COMPOSITOR_UX_PASS": earned,
            "compositor_output_count": outputs,
            "note": (
                "Two guest DRM outputs AND weston reporting >=2 real wl_output globals"
                if earned
                else (
                    "Not earned — guest_dual_output="
                    f"{gate.get('GUEST_DUAL_OUTPUT_PASS')} compositor_outputs={outputs}. "
                    "Two connected DRM connectors alone is insufficient; weston must report "
                    ">=2 real compositor output globals via wayland-info."
                )
            ),
        }
    )
    (evidence_dir / "DSXL_COMPOSITOR_UX_EVIDENCE.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def attempt_ring_app_mutation_pass(session: Any, evidence_dir: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"RING_TO_REAL_APP_STATE_MUTATION_PASS": False, "claim_boundary": CLAIM}
    doc_path = "/root/gunnchos-lab-document.txt"

    launch = _agent_call(session, "app_launch", app="mousepad", timeout_sec=15.0)
    result["app_launch"] = launch
    time.sleep(3.0)
    # Click to focus the editor surface, then End to append (avoid overwriting).
    _agent_call(session, "input_inject", kind="pointer", dx=200, dy=200, button="left", timeout_sec=10.0)
    time.sleep(0.3)
    _agent_call(session, "input_inject", kind="key", key="end", timeout_sec=5.0)
    time.sleep(0.2)

    before = _agent_call(session, "logs", path=doc_path, lines=50)
    result["document_before"] = before

    mutation_text = f"RINGMUTATION{int(time.time())}"
    inject = _agent_call(session, "input_inject", kind="text", text=mutation_text, timeout_sec=15.0)
    result["ring_input_inject"] = inject
    save = _agent_call(session, "input_inject", kind="key", key="s", mods=["ctrl"], timeout_sec=10.0)
    result["save_keystroke"] = save
    time.sleep(2.0)

    after = _agent_call(session, "logs", path=doc_path, lines=50)
    result["document_after"] = after

    before_text = "\n".join(before.get("lines") or [])
    after_text = "\n".join(after.get("lines") or [])
    mutated = bool(inject.get("ok") and mutation_text in after_text and after_text != before_text)

    result.update(
        {
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": mutated,
            "mutation_marker": mutation_text,
            "marker_found_in_after": mutation_text in after_text,
            "note": (
                "Real guest uinput text injection landed in the real in-guest mousepad "
                "document via HID->libinput->weston->app, verified by reading the saved file"
                if mutated
                else (
                    "Not earned — marker not found in guest document after injection; "
                    "app_launch/input_inject/save fields above show the honest blocker"
                )
            ),
        }
    )
    (evidence_dir / "RING_APP_MUTATION_EVIDENCE.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Attempt Interactive Guest LIVE/DSXL/RING proofs")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--dual", action="store_true", help="Boot with dual virtio-gpu outputs for DSXL attempt")
    parser.add_argument("--boot-timeout-s", type=int, default=180)
    parser.add_argument("--memory-mb", type=int, default=3072)
    ns = parser.parse_args(argv)

    repo_root = Path(ns.repo_root) if ns.repo_root else Path(__file__).resolve().parents[2]
    work = repo_root / "artifacts" / "wp011r" / "interactive_guest_session"
    boot = boot_interactive_guest(
        repo_root,
        work,
        dual=ns.dual,
        boot_timeout_s=ns.boot_timeout_s,
        memory_mb=ns.memory_mb,
    )
    session = boot.pop("_session", None)
    out: dict[str, Any] = {"boot": boot}
    if not boot.get("ok") or session is None:
        out["error"] = "interactive_guest_boot_failed"
        print(json.dumps(out, indent=2, default=str))
        return 1
    try:
        visual_dir = _evidence_dir(repo_root, "visual")
        dsxl_dir = _evidence_dir(repo_root, "dsxl")
        ring_dir = _evidence_dir(repo_root, "ring")
        # Give weston/openvt a few seconds after guest-agent ping before proofs.
        for _ in range(12):
            probe = _agent_call(session, "compositor_info", timeout_sec=10.0)
            if probe.get("available"):
                break
            time.sleep(2.0)
        out["live_visual"] = attempt_live_visual_pass(session, visual_dir)
        if ns.dual:
            out["dsxl"] = attempt_dsxl_dual_compositor_pass(session, dsxl_dir)
        out["ring"] = attempt_ring_app_mutation_pass(session, ring_dir)
    finally:
        try:
            session.stop()
        except Exception:  # noqa: BLE001
            pass
    print(json.dumps({k: v for k, v in out.items() if k != "boot"}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
