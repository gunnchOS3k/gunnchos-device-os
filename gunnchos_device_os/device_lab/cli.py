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
            repo_root=_repo_root(),
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
    if ns.image_cmd == "interactive-manifest":
        from gunnchos_device_os.device_lab.interactive_image_builder import InteractiveGuestImageBuilder

        ib = InteractiveGuestImageBuilder(_repo_root())
        return _out({"ok": True, "manifest_path": str(ib.write_manifest())})
    if ns.image_cmd == "interactive-disk":
        from gunnchos_device_os.device_lab.interactive_image_builder import InteractiveGuestImageBuilder

        ib = InteractiveGuestImageBuilder(_repo_root())
        return _out(ib.create_disk_placeholder(arch=ns.arch, size_gb=ns.disk_size_gb))
    if ns.image_cmd == "interactive-capability":
        from gunnchos_device_os.device_lab.interactive_image_builder import detect_build_capability

        return _out(detect_build_capability())
    return _out({"ok": False, "error": f"unknown_image_cmd:{ns.image_cmd}"})


def cmd_ecosystem(ns: argparse.Namespace) -> int:
    from gunnchos_device_os.device_lab.ecosystem import (
        active_ecosystem,
        ecosystem_topology,
        list_ecosystems,
        run_all_eco,
        run_eco001_smoke,
        run_eco_scenario,
        start_ecosystem,
        stop_ecosystem,
    )

    cmd = ns.ecosystem_cmd
    if cmd == "topology":
        return _out(ecosystem_topology())
    if cmd == "eco001":
        # Legacy smoke retained; prefer `ecosystem test ECO-001` for real depth.
        return _out(run_eco001_smoke(repo_root=_repo_root()))
    if cmd == "start":
        return _out(
            start_ecosystem(
                repo_root=_repo_root(),
                preset=getattr(ns, "preset", "full") or "full",
            )
        )
    if cmd == "status":
        if getattr(ns, "eco_id", None):
            from gunnchos_device_os.device_lab.ecosystem import get_ecosystem

            return _out(get_ecosystem(ns.eco_id).status())
        rt = active_ecosystem()
        if rt is None:
            return _out({"ok": True, "running": False, "ecosystems": list_ecosystems()})
        return _out(rt.status())
    if cmd == "stop":
        eco_id = getattr(ns, "eco_id", None)
        if not eco_id:
            rt = active_ecosystem()
            if rt is None:
                return _out({"ok": False, "error": "no_active_ecosystem"})
            eco_id = rt.eco_id
        return _out(stop_ecosystem(eco_id))
    if cmd == "graph":
        rt = active_ecosystem()
        if rt is None:
            return _out({"ok": False, "error": "no_active_ecosystem"})
        return _out(rt.graph())
    if cmd == "test":
        scenario = getattr(ns, "scenario", None) or "ECO-001"
        if scenario.upper() in {"ALL", "ECO-ALL"}:
            return _out(run_all_eco(repo_root=_repo_root()))
        return _out(run_eco_scenario(scenario, repo_root=_repo_root()))
    return _out({"ok": False, "error": f"unknown_ecosystem_cmd:{cmd}"})


def cmd_chaos(ns: argparse.Namespace) -> int:
    from gunnchos_device_os.device_lab.chaos import ChaosEngine
    from gunnchos_device_os.device_lab.session import get_session, start_session, stop_session

    root = _repo_root()
    from gunnchos_device_os.device_lab.session import lab_artifact_root

    evid = lab_artifact_root(root) / "chaos"
    engine = ChaosEngine(repo_root=root, evidence_dir=evid / time_tag())
    if ns.chaos_cmd == "catalog":
        return _out({"ok": True, "catalog": engine.catalog()})
    profile = getattr(ns, "device", None) or "handheld_hybrid"
    started = start_session(profile, repo_root=root)
    sess = get_session(started["instance_id"])
    try:
        if ns.chaos_cmd == "inject":
            result = engine.inject(ns.fault, session=sess)
            cleanup = engine.cleanup_all()
            result["cleanup"] = cleanup
            return _out(result)
        if ns.chaos_cmd == "suite":
            faults = ns.faults.split(",") if getattr(ns, "faults", None) else None
            return _out(engine.run_suite(session=sess, faults=faults))
        return _out({"ok": False, "error": f"unknown_chaos_cmd:{ns.chaos_cmd}"})
    finally:
        stop_session(sess.instance_id)


def time_tag() -> str:
    import time as _time

    return _time.strftime("%Y%m%dT%H%M%S", _time.gmtime())


def cmd_score(_: argparse.Namespace) -> int:
    import subprocess

    script = _repo_root() / "scripts" / "device_lab_score_from_register.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(_repo_root()),
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(_repo_root())},
        check=False,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.returncode != 0 and proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return int(proc.returncode)


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
    s.add_argument("journey", help="GOLDEN-01/04/05/06/07/08/09")
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
    si_sub.add_parser("interactive-manifest").set_defaults(func=cmd_image)
    interactive_disk_p = si_sub.add_parser("interactive-disk")
    interactive_disk_p.add_argument("--arch", default="aarch64")
    interactive_disk_p.add_argument("--disk-size-gb", type=int, default=8)
    interactive_disk_p.set_defaults(func=cmd_image)
    si_sub.add_parser("interactive-capability").set_defaults(func=cmd_image)

    se = sub.add_parser("ecosystem")
    se_sub = se.add_subparsers(dest="ecosystem_cmd", required=True)
    se_sub.add_parser("topology").set_defaults(func=cmd_ecosystem)
    se_sub.add_parser("eco001").set_defaults(func=cmd_ecosystem)
    start_e = se_sub.add_parser("start")
    start_e.add_argument("--preset", default="full", choices=["full", "compute"])
    start_e.set_defaults(func=cmd_ecosystem)
    st_e = se_sub.add_parser("status")
    st_e.add_argument("eco_id", nargs="?")
    st_e.set_defaults(func=cmd_ecosystem)
    stop_e = se_sub.add_parser("stop")
    stop_e.add_argument("eco_id", nargs="?")
    stop_e.set_defaults(func=cmd_ecosystem)
    se_sub.add_parser("graph").set_defaults(func=cmd_ecosystem)
    test_e = se_sub.add_parser("test")
    test_e.add_argument("scenario", nargs="?", default="ECO-001", help="ECO-001..010 or ALL")
    test_e.set_defaults(func=cmd_ecosystem)

    sc = sub.add_parser("chaos")
    sc_sub = sc.add_subparsers(dest="chaos_cmd", required=True)
    sc_sub.add_parser("catalog").set_defaults(func=cmd_chaos)
    inj = sc_sub.add_parser("inject")
    inj.add_argument("fault")
    inj.add_argument("--device", default="handheld_hybrid")
    inj.set_defaults(func=cmd_chaos)
    suite = sc_sub.add_parser("suite")
    suite.add_argument("--device", default="handheld_hybrid")
    suite.add_argument("--faults", help="Comma-separated fault ids")
    suite.set_defaults(func=cmd_chaos)

    sub.add_parser("score").set_defaults(func=cmd_score)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    return int(ns.func(ns))


if __name__ == "__main__":
    sys.exit(main())
