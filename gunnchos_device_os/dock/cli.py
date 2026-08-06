"""Dock validation / continuity CLI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .collector import collect_host_dock_signals
from .simulator import run_dock_simulation
from .validator import run_dock_validation


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gunnchos-dock-validate",
        description="Gate 1 dock continuity validation (simulation + host collector).",
    )
    p.add_argument(
        "--out",
        default="results/gate1/dock_evidence.json",
    )
    p.add_argument(
        "--simulate",
        action="store_true",
        default=True,
        help="Run software dock continuity simulation (default).",
    )
    p.add_argument(
        "--no-simulate",
        action="store_true",
        help="Skip simulation; host collector only.",
    )
    p.add_argument(
        "--collect-only",
        action="store_true",
        help="Emit host dock capability signals only.",
    )
    p.add_argument(
        "--physical-template",
        action="store_true",
        help="Write physical dock evidence template (still PENDING).",
    )
    return p


def physical_template() -> dict:
    from gunnchos_device_os.identity import new_dock_event_id, utc_now_iso

    return {
        "schema": "gunnchos.dock_evidence.v1",
        "capture_kind": "physical_dock_template",
        "event_id": new_dock_event_id("phys"),
        "timestamp": utc_now_iso(),
        "physical_dock": False,
        "checklist": {
            "device_id_recorded": None,
            "dock_id_recorded": None,
            "ports_observed": None,
            "display_before_after": None,
            "inputs_before_after": None,
            "network_before_after": None,
            "apps_preserved": None,
            "session_preserved": None,
            "save_checksum_matched": None,
            "audio_route_recorded": None,
            "power_state_recorded": None,
            "attach_latency_ms": None,
            "detach_latency_ms": None,
            "errors": None,
        },
        "status_tokens": ["PHYSICAL_DOCK_EVIDENCE_PENDING"],
        "claim_boundary": "Template only — physical dock evidence not complete.",
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out = Path(args.out)

    if args.physical_template:
        doc = physical_template()
        out = out.with_name("physical_dock_capture.json") if out.name == "dock_evidence.json" else out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(doc, indent=2))
        return 0

    if args.collect_only:
        doc = collect_host_dock_signals()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(doc, indent=2))
        return 0

    if args.no_simulate:
        evidence = run_dock_validation(simulate=False, collect_host=True, out_path=out)
    else:
        evidence = run_dock_validation(simulate=True, collect_host=True, out_path=out)

    print(json.dumps(evidence, indent=2))
    tokens = evidence.get("status_tokens") or []
    return 0 if "DOCK_CONTINUITY_SIMULATION_PASS" in tokens or args.no_simulate else 1


if __name__ == "__main__":
    raise SystemExit(main())
