"""DS-XL dual-output honesty gate.

Prefer two *real guest* outputs when QEMU/compositor supports them.
High-fidelity gate FAILS if only logical dual outputs are claimed as guest dual.

WP-011R: GUEST_DUAL_OUTPUT_PASS (DRM enum) is insufficient for
DSXL_DUAL_COMPOSITOR_UX_PASS — require compositor surfaces, window placement,
focus move, and disconnect/reconnect/layout restore evidence.
"""
from __future__ import annotations

from typing import Any


def classify_outputs(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    connected = [o for o in outputs if o.get("connected")]
    sources = {str(o.get("source") or "unknown") for o in connected}
    guest_sources = {
        "qemu_virtio_gpu",
        "qemu_guest",
        "guest_agent",
        "WaylandSession",
        "virtio-gpu",
    }
    logical_sources = {"profile_logical", "logical", "fallback"}
    guest_count = sum(
        1
        for o in connected
        if str(o.get("source") or "") in guest_sources
        or str(o.get("class") or "").startswith("guest")
    )
    logical_count = sum(
        1
        for o in connected
        if str(o.get("source") or "") in logical_sources
        or "logical" in str(o.get("source") or "").lower()
    )
    # guest_agent DRM connector enum alone is NOT a compositor surface (WP-011R).
    compositor_sources = {"WaylandSession", "qemu_virtio_gpu", "virtio-gpu"}
    compositor_surfaces = sum(
        1
        for o in connected
        if o.get("compositor_surface") is True
        or (
            str(o.get("source") or "") in compositor_sources
            and str(o.get("class") or "") != "guest_drm"
        )
    )
    return {
        "connected": len(connected),
        "guest_connected": guest_count,
        "logical_connected": logical_count,
        "compositor_surfaces": compositor_surfaces,
        "sources": sorted(sources),
        "outputs": connected,
    }


def high_fidelity_dual_gate(
    outputs: list[dict[str, Any]],
    *,
    claim_guest_dual: bool = False,
) -> dict[str, Any]:
    """Fail high-fidelity if claim_guest_dual but only logical dual present."""
    info = classify_outputs(outputs)
    two = info["connected"] >= 2
    guest_dual = info["guest_connected"] >= 2
    logical_only_dual = two and info["guest_connected"] < 2 and info["logical_connected"] >= 2

    if claim_guest_dual and logical_only_dual:
        return {
            "ok": False,
            "gate": "FAIL_LOGICAL_DUAL_CLAIMED_AS_GUEST",
            "GUEST_DUAL_OUTPUT_PASS": False,
            "DSXL_DUAL_COMPOSITOR_UX_PASS": False,
            "LOGICAL_DUAL_OK_FOR_BEHAVIORAL": True,
            **info,
            "note": (
                "Two logical compositor/profile outputs are fine for behavioral G06, "
                "but must not be labeled as real guest dual outputs."
            ),
            "SILICON_EXACT_EMULATION": False,
            "PHYSICAL_DUAL_PANEL": "PENDING",
        }

    if guest_dual:
        return {
            "ok": True,
            "gate": "PASS_GUEST_DUAL",
            "GUEST_DUAL_OUTPUT_PASS": True,
            "DSXL_DUAL_COMPOSITOR_UX_PASS": False,
            "note": (
                "DRM/guest dual enum earned GUEST_DUAL_OUTPUT_PASS only; "
                "DSXL_DUAL_COMPOSITOR_UX_PASS requires compositor_ux_gate evidence."
            ),
            **info,
            "SILICON_EXACT_EMULATION": False,
            "PHYSICAL_DUAL_PANEL": "PENDING",
        }

    if two:
        return {
            "ok": True,
            "gate": "PASS_LOGICAL_OR_COMPOSITOR_DUAL",
            "GUEST_DUAL_OUTPUT_PASS": False,
            "DSXL_DUAL_COMPOSITOR_UX_PASS": False,
            "LOGICAL_DUAL_OK_FOR_BEHAVIORAL": True,
            **info,
            "note": "Behavioral dual OK; guest dual not claimed; UX token not earned here",
            "SILICON_EXACT_EMULATION": False,
            "PHYSICAL_DUAL_PANEL": "PENDING",
        }

    return {
        "ok": False,
        "gate": "FAIL_ONE_DISPLAY",
        "GUEST_DUAL_OUTPUT_PASS": False,
        "DSXL_DUAL_COMPOSITOR_UX_PASS": False,
        **info,
        "SILICON_EXACT_EMULATION": False,
        "PHYSICAL_DUAL_PANEL": "PENDING",
    }


def compositor_ux_gate(
    *,
    outputs: list[dict[str, Any]],
    windows: list[dict[str, Any]] | None = None,
    focus_moves: list[dict[str, Any]] | None = None,
    disconnect_reconnect: dict[str, Any] | None = None,
    layout_restore: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Earn DSXL_DUAL_COMPOSITOR_UX_PASS only with full UX evidence beyond DRM enum."""
    info = classify_outputs(outputs)
    windows = windows or []
    focus_moves = focus_moves or []
    disconnect_reconnect = disconnect_reconnect or {}
    layout_restore = layout_restore or {}

    two_outputs = info["connected"] >= 2
    two_surfaces = info["compositor_surfaces"] >= 2
    # Distinct output_ids with at least one window each
    by_out: dict[str, int] = {}
    for w in windows:
        oid = str(w.get("output_id") or "")
        if oid:
            by_out[oid] = by_out.get(oid, 0) + 1
    placement_ok = len([k for k, n in by_out.items() if n > 0]) >= 2
    focus_ok = any(bool(f.get("ok")) for f in focus_moves) and len(focus_moves) >= 1
    # Prefer evidence of focus moving between two different outputs
    focus_outputs = {
        str(f.get("output_id") or (f.get("focus") or {}).get("output_id") or "")
        for f in focus_moves
        if f.get("ok")
    }
    focus_cross = len([o for o in focus_outputs if o]) >= 2
    disc = bool(disconnect_reconnect.get("disconnect_ok"))
    recon = bool(disconnect_reconnect.get("reconnect_ok"))
    restore = bool(
        layout_restore.get("ok")
        or layout_restore.get("layout_restored")
        or disconnect_reconnect.get("layout_restored")
    )

    earned = bool(
        two_outputs
        and two_surfaces
        and placement_ok
        and focus_ok
        and focus_cross
        and disc
        and recon
        and restore
    )
    missing: list[str] = []
    if not two_outputs:
        missing.append("two_connected_outputs")
    if not two_surfaces:
        missing.append("two_compositor_surfaces")
    if not placement_ok:
        missing.append("window_placement_on_both_outputs")
    if not (focus_ok and focus_cross):
        missing.append("focus_move")
    if not disc:
        missing.append("disconnect")
    if not recon:
        missing.append("reconnect")
    if not restore:
        missing.append("layout_restore")

    return {
        "ok": earned,
        "gate": "PASS_DSXL_COMPOSITOR_UX" if earned else "FAIL_DSXL_COMPOSITOR_UX",
        "DSXL_DUAL_COMPOSITOR_UX_PASS": earned,
        "GUEST_DUAL_OUTPUT_PASS_insufficient_alone": True,
        "checks": {
            "two_outputs": two_outputs,
            "two_compositor_surfaces": two_surfaces,
            "window_placement": placement_ok,
            "focus_move": focus_ok and focus_cross,
            "disconnect": disc,
            "reconnect": recon,
            "layout_restore": restore,
        },
        "missing": missing,
        "windows": windows,
        "focus_moves": focus_moves,
        "disconnect_reconnect": disconnect_reconnect,
        "layout_restore": layout_restore,
        **info,
        "SILICON_EXACT_EMULATION": False,
        "PHYSICAL_DUAL_PANEL": "PENDING",
        "note": (
            "DSXL UX PASS earned"
            if earned
            else "DRM enum / dual connected alone insufficient; missing: " + ",".join(missing)
        ),
    }
