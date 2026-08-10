"""DS-XL dual-output honesty gate.

Prefer two *real guest* outputs when QEMU/compositor supports them.
High-fidelity gate FAILS if only logical dual outputs are claimed as guest dual.
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
    return {
        "connected": len(connected),
        "guest_connected": guest_count,
        "logical_connected": logical_count,
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
            **info,
            "SILICON_EXACT_EMULATION": False,
            "PHYSICAL_DUAL_PANEL": "PENDING",
        }

    if two:
        return {
            "ok": True,
            "gate": "PASS_LOGICAL_OR_COMPOSITOR_DUAL",
            "GUEST_DUAL_OUTPUT_PASS": False,
            "LOGICAL_DUAL_OK_FOR_BEHAVIORAL": True,
            **info,
            "note": "Behavioral dual OK; guest dual not claimed",
            "SILICON_EXACT_EMULATION": False,
            "PHYSICAL_DUAL_PANEL": "PENDING",
        }

    return {
        "ok": False,
        "gate": "FAIL_ONE_DISPLAY",
        "GUEST_DUAL_OUTPUT_PASS": False,
        **info,
        "SILICON_EXACT_EMULATION": False,
        "PHYSICAL_DUAL_PANEL": "PENDING",
    }
