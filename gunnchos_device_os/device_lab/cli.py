"""gunnchctl — gunnchDevice Lab developer CLI."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _out(data: Any) -> int:
    print(json.dumps(data, indent=2, default=str))
    if isinstance(data, dict) and "ok" in data:
        return 0 if data.get("ok") else 1
    return 0


def cmd_devices(_: argparse.Namespace) -> int:
    from gunnchos_device_os.device_lab.profiles import list_profiles, load_profile

    rows = []
    for pid in list_profiles():
        p = load_profile(pid)
        rows.append(
            {
                "profile_id": pid,
                "product": p.get("product"),
                "fidelity_level": p.get("fidelity_level"),
                "display_outputs": len(p.get("display_outputs") or []),
                "ram_gb": (p.get("ram") or {}).get("gb"),
                "compute_mpn": (p.get("compute") or {}).get("mpn")
                or (p.get("exact_mpns") or {}).get("compute"),
            }
        )
    return _out({"ok": True, "devices": rows})


def cmd_start(ns: argparse.Namespace) -> int:
    from gunnchos_device_os.device_lab.session import start_session

    if getattr(ns, "real_guest", False):
        os.environ["GUNNCHDEVICE_LAB_FORCE_REAL_GUEST"] = "1"
        os.environ.setdefault("GUNNCHDEVICE_LAB_BACKEND", "QEMU_TCG")
    return _out(start_session(ns.profile, repo_root=_repo_root()))


def cmd_stop(ns: argparse.Namespace) -> int:
    from gunnchos_device_os.device_lab.session import stop_session

    return _out(stop_session(ns.instance))


def cmd_status(ns: argparse.Namespace) -> int:
    from gunnchos_device_os.device_lab.session import get_session, list_sessions

    if ns.instance:
        return _out(get_session(ns.instance).status())
    return _out({"ok": True, "sessions": list_sessions()})


def cmd_run(ns: argparse.Namespace) -> int:
    from gunnchos_device_os.device_lab.apps.runner import run_app
    from gunnchos_device_os.device_lab.session import get_qemu_session, get_session, start_session, stop_session

    if getattr(ns, "real_guest", False):
        os.environ["GUNNCHDEVICE_LAB_FORCE_REAL_GUEST"] = "1"
        os.environ.setdefault("GUNNCHDEVICE_LAB_BACKEND", "QEMU_TCG")
    started = start_session(ns.device, repo_root=_repo_root())
    sess = get_session(started["instance_id"])
    try:
        agent = None
        q = get_qemu_session(sess.instance_id)
        if q is not None:
            agent = getattr(q, "agent", None)
        launch = run_app(
            app=ns.app,
            work=sess.work,
            agent=agent,
            prefer_guest=bool(agent is not None),
            keep=bool(ns.keep),
        )
        result = {
            **launch,
            "instance_id": sess.instance_id,
            "profile_id": sess.profile_id,
            "session_ok": started.get("ok"),
            "qemu": (started.get("state") or {}).get("qemu"),
            "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
            "SILICON_EXACT_EMULATION": False,
        }
        # Refuse intent-only labeling
        result["intent_only"] = False
        (sess.work / "run_app.json").write_text(
            json.dumps(result, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        return _out(result)
    finally:
        if not ns.keep:
            stop_session(sess.instance_id)


def cmd_scenario(ns: argparse.Namespace) -> int:
    from gunnchos_device_os.device_lab.scenarios.engine import run_scenario

    return _out(
        run_scenario(
            ns.scenario,
            profile_id=ns.device,
            repo_root=_repo_root(),
            instance_id=ns.instance,
        )
    )


def cmd_test(ns: argparse.Namespace) -> int:
    from gunnchos_device_os.device_lab.scenarios.catalog import JOURNEY_SCENARIO_MAP
    from gunnchos_device_os.device_lab.scenarios.engine import run_scenario

    journey = ns.journey.upper().replace("_", "-")
    if not journey.startswith("GOLDEN-"):
        journey = f"GOLDEN-{journey.replace('GOLDEN', '').lstrip('-')}"
    # normalize GOLDEN-4 -> GOLDEN-04
    if journey.startswith("GOLDEN-") and len(journey.split("-")[1]) == 1:
        journey = f"GOLDEN-0{journey.split('-')[1]}"
    meta = JOURNEY_SCENARIO_MAP.get(journey)
    if not meta:
        return _out({"ok": False, "error": f"unsupported_journey:{ns.journey}"})
    profile = ns.device or meta["profile"]
    result = run_scenario(journey, profile_id=profile, repo_root=_repo_root())
    result["rings_flag"] = bool(ns.rings)
    result["offline_flag"] = bool(ns.offline)
    return _out(result)


def cmd_evidence(ns: argparse.Namespace) -> int:
    root = _repo_root() / "artifacts" / "device_lab"
    matches = list(root.rglob("run_manifest.json")) if root.exists() else []
    if ns.run_id:
        for m in matches:
            data = json.loads(m.read_text(encoding="utf-8"))
            if data.get("run_id") == ns.run_id:
                return _out({"ok": True, "manifest": data, "path": str(m)})
        return _out({"ok": False, "error": "run_id_not_found", "run_id": ns.run_id})
    return _out(
        {
            "ok": True,
            "count": len(matches),
            "runs": [
                {
                    "path": str(m),
                    "run_id": json.loads(m.read_text(encoding="utf-8")).get("run_id"),
                }
                for m in matches[-20:]
            ],
        }
    )


def cmd_compare(ns: argparse.Namespace) -> int:
    from gunnchos_device_os.device_lab.profiles import compare_profiles

    return _out({"ok": True, **compare_profiles(ns.profile_a, ns.profile_b)})


def cmd_ui(ns: argparse.Namespace) -> int:
    from gunnchos_device_os.device_lab.ui.server import serve

    return serve(host=ns.host, port=ns.port)


def cmd_profile(ns: argparse.Namespace) -> int:
    from gunnchos_device_os.device_lab.profile_sync import diff_profiles, sync_profiles, verify_profiles

    if ns.profile_cmd == "sync":
        return _out(sync_profiles(write=not ns.dry_run))
    if ns.profile_cmd == "verify":
        return _out(verify_profiles())
    if ns.profile_cmd == "diff":
        return _out(diff_profiles())
    return _out({"ok": False, "error": f"unknown_profile_cmd:{ns.profile_cmd}"})


def cmd_image(ns: argparse.Namespace) -> int:
    from gunnchos_device_os.device_lab.image_builder import LabGuestImageBuilder

    builder = LabGuestImageBuilder(_repo_root())
    if ns.image_cmd == "build":
        return _out(builder.build(fetch=not ns.offline))
    if ns.image_cmd == "inspect":
        return _out(builder.inspect())
    if ns.image_cmd == "verify":
        return _out(builder.verify())
    return _out({"ok": False, "error": f"unknown_image_cmd:{ns.image_cmd}"})


def cmd_ecosystem(ns: argparse.Namespace) -> int:
    from gunnchos_device_os.device_lab.ecosystem import ecosystem_topology, run_eco001_smoke

    if ns.ecosystem_cmd == "topology":
        return _out(ecosystem_topology())
    if ns.ecosystem_cmd == "eco001":
        return _out(run_eco001_smoke(repo_root=_repo_root()))
    return _out({"ok": False, "error": f"unknown_ecosystem_cmd:{ns.ecosystem_cmd}"})


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gunnchctl", description="gunnchDevice Lab CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("devices").set_defaults(func=cmd_devices)

    s = sub.add_parser("start")
    s.add_argument("profile")
    s.add_argument(
        "--real-guest",
        action="store_true",
        help="Force real QEMU guest (HVF/KVM/TCG) instead of hybrid-only",
    )
    s.set_defaults(func=cmd_start)

    s = sub.add_parser("stop")
    s.add_argument("instance")
    s.set_defaults(func=cmd_stop)

    s = sub.add_parser("status")
    s.add_argument("instance", nargs="?")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("run")
    s.add_argument("app")
    s.add_argument("--device", required=True)
    s.add_argument("--keep", action="store_true")
    s.add_argument(
        "--real-guest",
        action="store_true",
        help="Prefer QEMU guest process_start when available",
    )
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("scenario")
    s.add_argument("scenario")
    s.add_argument("--device")
    s.add_argument("--instance")
    s.set_defaults(func=cmd_scenario)

    s = sub.add_parser("test")
    s.add_argument("journey", help="GOLDEN-04/06/07/08")
    s.add_argument("--device")
    s.add_argument("--rings", action="store_true")
    s.add_argument("--offline", action="store_true")
    s.set_defaults(func=cmd_test)

    s = sub.add_parser("evidence")
    s.add_argument("run_id", nargs="?")
    s.set_defaults(func=cmd_evidence)

    s = sub.add_parser("compare")
    s.add_argument("profile_a")
    s.add_argument("profile_b")
    s.set_defaults(func=cmd_compare)

    s = sub.add_parser("ui")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8765)
    s.set_defaults(func=cmd_ui)

    sp = sub.add_parser("profile")
    sp_sub = sp.add_subparsers(dest="profile_cmd", required=True)
    sync_p = sp_sub.add_parser("sync")
    sync_p.add_argument("--dry-run", action="store_true")
    sync_p.set_defaults(func=cmd_profile)
    sp_sub.add_parser("verify").set_defaults(func=cmd_profile)
    sp_sub.add_parser("diff").set_defaults(func=cmd_profile)

    si = sub.add_parser("image")
    si_sub = si.add_subparsers(dest="image_cmd", required=True)
    build_i = si_sub.add_parser("build")
    build_i.add_argument("--offline", action="store_true", help="Do not fetch Alpine cache")
    build_i.set_defaults(func=cmd_image)
    si_sub.add_parser("inspect").set_defaults(func=cmd_image)
    si_sub.add_parser("verify").set_defaults(func=cmd_image)

    se = sub.add_parser("ecosystem")
    se_sub = se.add_subparsers(dest="ecosystem_cmd", required=True)
    se_sub.add_parser("topology").set_defaults(func=cmd_ecosystem)
    se_sub.add_parser("eco001").set_defaults(func=cmd_ecosystem)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    return int(ns.func(ns))


if __name__ == "__main__":
    sys.exit(main())
