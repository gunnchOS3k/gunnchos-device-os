#!/usr/bin/env python3
"""Package already-earned Interactive Guest evidence into product-use journey packs.

Does not re-boot the guest. Use after product_use_run_journeys.py (or equivalent)
has written artifacts/wp011r/{visual,dsxl,ring}/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.product_use_run_journeys import (  # noqa: E402
    OUT,
    _copy_tree,
    _utc,
    _waike_teacher_isolation,
    _write_persona_table,
)


def main() -> int:
    live_path = ROOT / "artifacts/wp011r/visual/LIVE_VISUAL_EVIDENCE.json"
    dsxl_path = ROOT / "artifacts/wp011r/dsxl/DSXL_COMPOSITOR_UX_EVIDENCE.json"
    ring_path = ROOT / "artifacts/wp011r/ring/RING_APP_MUTATION_EVIDENCE.json"
    boot_path = OUT / "boot.json"

    live = json.loads(live_path.read_text()) if live_path.exists() else {"ok": False}
    dsxl = json.loads(dsxl_path.read_text()) if dsxl_path.exists() else {"ok": False}
    ring = json.loads(ring_path.read_text()) if ring_path.exists() else {"ok": False}
    boot = json.loads(boot_path.read_text()) if boot_path.exists() else {"ok": False}

    # Normalize PASS flags used by table writer
    live["ok"] = bool(live.get("LIVE_GUNNCHOS_VISUAL_PASS"))
    live["LIVE_GUNNCHOS_VISUAL_PASS"] = bool(live.get("LIVE_GUNNCHOS_VISUAL_PASS"))
    dsxl_pass = bool(
        dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS") or dsxl.get("DSXL_DUAL_COMPOSITOR_PASS")
    )
    dsxl["ok"] = dsxl_pass
    dsxl["DSXL_DUAL_COMPOSITOR_PASS"] = dsxl_pass
    ring_pass = bool(
        ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS") or ring.get("RING_APP_MUTATION_PASS")
    )
    ring["ok"] = ring_pass
    ring["RING_APP_MUTATION_PASS"] = ring_pass

    waike = _waike_teacher_isolation()
    (OUT / "waike_teacher_isolation.json").write_text(json.dumps(waike, indent=2) + "\n")

    live_copy = _copy_tree(ROOT / "artifacts/wp011r/visual", OUT / "G12_G11_live_visual")
    dsxl_copy = _copy_tree(ROOT / "artifacts/wp011r/dsxl", OUT / "G14_dsxl")
    ring_copy = _copy_tree(ROOT / "artifacts/wp011r/ring", OUT / "G11_ring")

    # Capture DSXL partial (windows placed) even when UX PASS false
    dsxl_partial = {
        "DSXL_DUAL_COMPOSITOR_UX_PASS": dsxl_pass,
        "dual_windows_placed": bool(
            ((dsxl.get("compositor_ux_gate") or {}).get("windows") or [])
        ),
        "windows": (dsxl.get("compositor_ux_gate") or {}).get("windows"),
        "missing": (dsxl.get("compositor_ux_gate") or {}).get("missing"),
        "png_captures": [
            str(p.relative_to(ROOT))
            for p in (OUT / "G14_dsxl").glob("*.png")
        ]
        if (OUT / "G14_dsxl").exists()
        else [],
        "observation_class": (
            "GUEST_OBSERVED" if dsxl_pass else (
                "GUEST_OBSERVED_PARTIAL_DUAL_PLACEMENT"
                if (dsxl.get("compositor_ux_gate") or {}).get("windows")
                else "FAIL"
            )
        ),
    }
    (OUT / "dsxl_partial.json").write_text(json.dumps(dsxl_partial, indent=2) + "\n")

    summary = {
        "schema": "gunnchos.product_use_rc_001.journey_run.v1",
        "packaged_at_utc": _utc(),
        "source": "artifacts/wp011r after product_use_run_journeys Interactive Guest boot",
        "prefer_fail_over_false_pass": True,
        "boot": boot,
        "live_visual": {
            "ok": live["ok"],
            "LIVE_GUNNCHOS_VISUAL_PASS": live["LIVE_GUNNCHOS_VISUAL_PASS"],
            "observation_class": "GUEST_OBSERVED" if live["ok"] else "FAIL",
            "evidence_copy": live_copy,
            "typed_marker_found": bool(
                (live.get("input_visible_app_state") or {}).get("found_in_document")
            ),
        },
        "dsxl": {
            "ok": dsxl_pass,
            "DSXL_DUAL_COMPOSITOR_UX_PASS": dsxl_pass,
            "observation_class": dsxl_partial["observation_class"],
            "evidence_copy": dsxl_copy,
            "partial": dsxl_partial,
        },
        "ring": {
            "ok": ring_pass,
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": ring_pass,
            "observation_class": "GUEST_OBSERVED" if ring_pass else "FAIL",
            "evidence_copy": ring_copy,
            "mutations": {
                "libreoffice": bool(((ring.get("mutations") or {}).get("libreoffice") or {}).get("mutated")
                                    or ((ring.get("mutations") or {}).get("libreoffice") or {}).get("odt_probe")),
                "browser": bool(((ring.get("mutations") or {}).get("browser") or {}).get("mutated")),
                "game": bool(((ring.get("mutations") or {}).get("game") or {}).get("mutated")),
            },
        },
        "waike_teacher_isolation": waike,
        "VISUAL_MODEL_REVIEW": (
            "AVAILABLE_CAPTURES"
            if list((OUT / "G14_dsxl").glob("*.png"))
            else "UNAVAILABLE"
        ),
        "handheld_dock_continuity": "OPEN",
        "persona_tokens_all_false": True,
        "claim_boundary": (
            "Finite Interactive Guest subset. Persona pickup-and-use tokens remain false. "
            "Cursor does not merge. Beat Link #20 BRANCH_EVIDENCE until Edmund merges."
        ),
    }

    # Enrich G14 mapping: allow partial dual placement in table via dsxl ok=False but
    # custom note — adjust writer inputs: keep dsxl ok false; table already handles.
    # For G14 primary_task, patch after write if partial.
    table = _write_persona_table(summary, live, dsxl, ring, waike)
    g14 = next(r for r in table["rows"] if r["persona"] == "G14")
    if not dsxl_pass and dsxl_partial.get("dual_windows_placed"):
        g14["boot"] = "GUEST_OBSERVED:interactive_guest_boot" if boot.get("ok") else g14["boot"]
        g14["primary_task"] = (
            "GUEST_OBSERVED_PARTIAL:dual_window_placement_pngs;"
            "DSXL_DUAL_COMPOSITOR_UX_PASS=false(missing_focus_move)"
        )
        g14["apps"] = "GUEST_OBSERVED_PARTIAL:foot+mousepad_on_two_outputs"
        g14["artifact"] = "GUEST_OBSERVED:dsxl_left/right/placement.png"
        g14["evidence"] = "artifacts/product_use/journeys/G14_dsxl"
        g14["terminal"] = "GUEST_OBSERVED:foot_present_builder_allowed"
        g14["developer_intervention"] = "AUTOMATED_GUEST_AGENT"
        g14["VISUAL_MODEL_REVIEW"] = summary["VISUAL_MODEL_REVIEW"]
        g14["S1"] = 1
        g14["S2"] = 1
        g14["token_earned"] = False
    table["rows"] = [g14 if r["persona"] == "G14" else r for r in table["rows"]]
    table["VISUAL_MODEL_REVIEW"] = summary["VISUAL_MODEL_REVIEW"]
    table["handheld_dock_continuity"] = "OPEN"
    table["ring_mutation"] = "GUEST_OBSERVED" if ring_pass else "OPEN"
    (ROOT / "artifacts/product_use/PERSONA_JOURNEY_TABLE.json").write_text(
        json.dumps(table, indent=2) + "\n"
    )

    summary["persona_table_path"] = "artifacts/product_use/PERSONA_JOURNEY_TABLE.json"
    summary["tokens_earned"] = {row["token_id"]: row["token_earned"] for row in table["rows"]}
    (OUT / "RUN_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")

    # Update status artifact
    status_path = ROOT / "artifacts/product_use/PRODUCT_USE_RC_001_STATUS.json"
    status = json.loads(status_path.read_text()) if status_path.exists() else {}
    status.update(
        {
            "journey_run": summary,
            "VISUAL_MODEL_REVIEW": summary["VISUAL_MODEL_REVIEW"],
            "ring_mutation": summary["ring"]["observation_class"],
            "handheld_dock_continuity": "OPEN",
            "persona_tokens": summary["tokens_earned"],
            "updated_at_utc": _utc(),
            "S1_open": [
                "Full G11–G15 pickup-and-use tokens not earned",
                "G14 DSXL_DUAL_COMPOSITOR_UX_PASS false (missing focus_move)",
                "G15 creative mature in-guest app NOT_RUN",
                "Handheld dock continuity OPEN",
                "In-guest WAIKE UI / AI journeys NOT_RUN (ingest HOST_OBSERVED only)",
                "Reboot/resume continuity NOT_RUN",
            ],
            "S2_open": [
                "REAL_TEACHER_E6=false",
                "HUMAN_E6",
                "Beat Link #20 BRANCH_EVIDENCE until Edmund merge",
                "gunnchAI #34 BRANCH_EVIDENCE; journeys use accepted main only",
            ],
            "S0_open": 0,
        }
    )
    status_path.write_text(json.dumps(status, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
