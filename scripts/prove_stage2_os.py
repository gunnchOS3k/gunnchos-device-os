#!/usr/bin/env python3
"""Prove Stage 2 OS foundations — DIGITALLY_VALIDATED only where tests pass."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "stage2"
sys.path.insert(0, str(ROOT))

DIGITALLY_VALIDATED = "DIGITALLY_VALIDATED"
INCOMPLETE_DIGITAL = "INCOMPLETE_DIGITAL"


def run_pytest(nodeid: str) -> dict:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", nodeid],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": f"{ROOT}:src"},
    )
    return {
        "nodeid": nodeid,
        "rc": r.returncode,
        "out": (r.stdout or "")[-1500:],
        "err": (r.stderr or "")[-1500:],
    }


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    from gunnchos_device_os.stage2.image_build import build_image
    from gunnchos_device_os.stage2.update_manager import UpdateManager
    from gunnchos_device_os.stage2.recovery import RecoveryEnv
    from gunnchos_device_os.stage2.shell.contract import ShellContract
    from gunnchos_device_os.stage2.shell.profiles import AdaptiveProfile
    from gunnchos_device_os.stage2.compat.corpus import run_corpus
    from gunnchos_device_os.stage2.compat.registry import CompatRegistry, RuntimeLane
    from gunnchos_device_os.stage2.compat.proton import run_redistributable_test_app
    from gunnchos_device_os.stage2.security.sandbox import SandboxEnforcer, SandboxProfile, Permission
    from gunnchos_device_os.stage2.security.modes import ModeManager, SecurityMode
    from gunnchos_device_os.stage2.security.trust import TrustChain

    tokens: dict[str, bool] = {}
    gates: dict[str, str] = {}
    details: dict[str, object] = {}

    # Gate: OS base image
    img = build_image(repo_root=ROOT)
    tokens["OS_BASE_IMAGE_REAL"] = bool(img.get("ok"))
    gates["frontier-os-base"] = DIGITALLY_VALIDATED if img.get("ok") else INCOMPLETE_DIGITAL
    details["image"] = {k: v for k, v in img.items() if k != "manifest"}

    # Gate: atomic update + rollback
    with tempfile.TemporaryDirectory(prefix="stage2-upd-") as tmp:
        # Prefer artifacts sysroot if image built; else temp
        sysroot = ROOT / "artifacts" / "stage2" / "prove_sysroot"
        if sysroot.exists():
            import shutil

            shutil.rmtree(sysroot)
        mgr = UpdateManager(sysroot)
        # seed user data
        (sysroot / "data" / "appstate.json").write_text('{"ok":true}\n')
        success = mgr.run_success_path()
        # fresh manager state for failure — keep user data
        fail = mgr.run_failure_rollback_path()
        atomic_ok = bool(success.get("ok") and fail.get("ok"))
        tokens["ATOMIC_UPDATE_ROLLBACK_DIGITAL_PASS"] = atomic_ok
        gates["atomic-update-rollback"] = (
            DIGITALLY_VALIDATED if atomic_ok else INCOMPLETE_DIGITAL
        )
        details["atomic"] = {"success": success, "failure": fail}

    # Gate: recovery
    rec = RecoveryEnv(ROOT / "artifacts" / "stage2" / "prove_sysroot")
    inspect = rec.inspect_slots()
    repair = rec.repair_metadata()
    diag = rec.export_diagnostics(ART / "RECOVERY_DIAGNOSTICS.json")
    # factory reset requires explicit flag
    denied = rec.factory_reset_user_data(confirm=False)
    reset = rec.factory_reset_user_data(confirm=True)
    recovery_ok = (
        inspect.get("active") is not None
        and repair.get("ok")
        and diag.get("ok")
        and denied.get("ok") is False
        and reset.get("ok") is True
    )
    # reinstall if manifest exists
    manifest = ROOT / "artifacts" / "stage2" / "image" / "MANIFEST.json"
    if manifest.exists():
        # rebuild sysroot slots after factory reset for reinstall test
        from gunnchos_device_os.stage2.filesystem import ensure_sysroot
        from gunnchos_device_os.stage2.update_manager import UpdateManager as UM

        ensure_sysroot(ROOT / "artifacts" / "stage2" / "prove_sysroot")
        UM(ROOT / "artifacts" / "stage2" / "prove_sysroot")
        reinstall = RecoveryEnv(ROOT / "artifacts" / "stage2" / "prove_sysroot").reinstall_approved_image(
            manifest
        )
        recovery_ok = recovery_ok and bool(reinstall.get("ok"))
        details["reinstall"] = reinstall
    tokens["RECOVERY_DIGITAL_PASS"] = recovery_ok
    gates["recovery"] = DIGITALLY_VALIDATED if recovery_ok else INCOMPLETE_DIGITAL
    details["recovery"] = {
        "inspect": inspect,
        "repair": repair,
        "factory_reset_denied": denied,
        "factory_reset": reset,
    }

    # Gate: shell profiles
    shell = ShellContract(AdaptiveProfile.HANDHELD_GAMEPAD)
    for surface in (
        "open_launcher",
        "manage_window",
        "set_quick_setting",
        "notify",
        "media_control",
        "search",
        "file_share_action",
        "session_info",
        "set_accessibility",
    ):
        getattr(shell, surface)  # existence
    shell.open_launcher()
    shell.manage_window("focus")
    shell.set_quick_setting("wifi", False)
    shell.notify("stage2")
    shell.media_control("play", "demo")
    shell.search("docs")
    shell.file_share_action("/data/file.txt")
    shell.set_accessibility(screen_reader=True)
    seq = shell.run_transition(["dock", "desktop", "undock"])
    ds = ShellContract(AdaptiveProfile.DSXL_DUAL_SCREEN)
    ds_seq = ds.run_transition(["external_attach", "external_detach"])
    shell_ok = (
        seq[0]["profile"] == "HANDHELD_DOCKED"
        and seq[1]["profile"] == "STUDENT_DESKTOP"
        and seq[2]["profile"] == "HANDHELD_GAMEPAD"
        and ds_seq[0]["dual_screen"] is True
        and ds_seq[1]["profile"] == "STUDENT_DESKTOP"
        and shell.compositor == "weston"
    )
    tokens["SHELL_PROFILES_DIGITAL_PASS"] = shell_ok
    gates["shell-profiles"] = DIGITALLY_VALIDATED if shell_ok else INCOMPLETE_DIGITAL
    details["shell"] = {"handheld_seq": seq, "dsxl_seq": ds_seq}

    # Gate: compatibility corpus
    reg = CompatRegistry()
    android = reg.get(RuntimeLane.ANDROID_EXPERIMENTAL)
    corpus = run_corpus()
    proton = run_redistributable_test_app(None)
    compat_ok = (
        corpus.get("ok")
        and android.evaluated is False
        and not corpus.get("fake_pass_detected")
        and proton["class"] == "UNKNOWN"  # no fixture → honest UNKNOWN
    )
    tokens["COMPAT_CORPUS_DIGITAL_PASS"] = compat_ok
    gates["compatibility-corpus"] = DIGITALLY_VALIDATED if compat_ok else INCOMPLETE_DIGITAL
    details["compat"] = {"corpus": corpus, "proton": proton, "lanes": reg.list_lanes()}

    # Gate: sandbox security
    sec_dir = ART / "security_state"
    if sec_dir.exists():
        import shutil

        shutil.rmtree(sec_dir)
    enf = SandboxEnforcer(sec_dir)
    enf.set_profile(
        SandboxProfile(
            "demo.app",
            allow={Permission.NET, Permission.FS_HOME},
            deny={Permission.FS_SYSTEM},
        )
    )
    deny = enf.check("demo.app", Permission.FS_SYSTEM)
    enf.revoke("demo.app", Permission.NET)
    deny2 = enf.check("demo.app", Permission.NET)
    enf.isolate_user("alice")
    enf.secret_put("alice", "token", "s3cret")
    secret_ok = enf.secret_get("alice", "token") == "s3cret"
    modes = ModeManager(sec_dir / "modes")
    esc = modes.escalate(SecurityMode.SECURE_DEVELOPER, reason="stage2-prove")
    rev = modes.revert()
    trust = TrustChain(sec_dir / "trust")
    # anti-rollback
    bad = {
        "schema": "t",
        "security_version": 0,
        "realm": "gunnchos-stage2-dev-signing-v1",
        "artifact_sha256": "0" * 64,
    }
    from gunnchos_device_os.stage2.crypto_dev import sign_payload

    bad["signature"] = sign_payload(bad)
    arb = trust.verify_update_metadata(bad)
    sec_ok = (
        deny["decision"] == "deny"
        and deny2["decision"] == "deny"
        and secret_ok
        and esc.get("logged")
        and rev.get("ok")
        and rev.get("reversible")
        and arb.get("reason") == "anti_rollback"
    )
    tokens["SANDBOX_SECURITY_DIGITAL_PASS"] = sec_ok
    gates["sandbox-security"] = DIGITALLY_VALIDATED if sec_ok else INCOMPLETE_DIGITAL
    details["security"] = {
        "denial": deny,
        "revocation_denial": deny2,
        "escalate": esc,
        "revert": rev,
        "anti_rollback": arb,
        "bwrap": enf.bubblewrap_available(),
    }

    # pytest suite (authoritative CI signal)
    pytest_jobs = {
        "frontier-os-base": "tests/stage2/test_os_base.py",
        "atomic-update-rollback": "tests/stage2/test_atomic_update.py",
        "recovery": "tests/stage2/test_recovery.py",
        "shell-profiles": "tests/stage2/test_shell.py",
        "compatibility-corpus": "tests/stage2/test_compat.py",
        "sandbox-security": "tests/stage2/test_security.py",
    }
    pytest_results = {}
    for gate, node in pytest_jobs.items():
        pr = run_pytest(node)
        pytest_results[gate] = pr
        if pr["rc"] != 0:
            gates[gate] = INCOMPLETE_DIGITAL
            # clear corresponding token
            for tok, gname in (
                ("OS_BASE_IMAGE_REAL", "frontier-os-base"),
                ("ATOMIC_UPDATE_ROLLBACK_DIGITAL_PASS", "atomic-update-rollback"),
                ("RECOVERY_DIGITAL_PASS", "recovery"),
                ("SHELL_PROFILES_DIGITAL_PASS", "shell-profiles"),
                ("COMPAT_CORPUS_DIGITAL_PASS", "compatibility-corpus"),
                ("SANDBOX_SECURITY_DIGITAL_PASS", "sandbox-security"),
            ):
                if gname == gate:
                    tokens[tok] = False

    report = {
        "schema": "gunnchos.stage2.os_prove_report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "physical_execution_freeze": True,
        "auto_merge_request": None,
        "frontier_os_parity_claimed": False,
        "GUNNCHOS_FRONTIER_OS_PARITY": False,
        "gates": gates,
        "tokens": tokens,
        "digitally_validated_gates": sorted(
            g for g, s in gates.items() if s == DIGITALLY_VALIDATED
        ),
        "incomplete_gates": sorted(
            g for g, s in gates.items() if s != DIGITALLY_VALIDATED
        ),
        "pytest": {k: {"rc": v["rc"]} for k, v in pytest_results.items()},
        "details": details,
    }
    def _scrub(obj):
        if isinstance(obj, dict):
            return {k: _scrub(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_scrub(x) for x in obj]
        if isinstance(obj, str) and ("/Users/" in obj or obj.startswith("/home/")):
            # keep basename-ish relative hint only
            return "artifacts/stage2/(scrubbed)"
        return obj

    report = _scrub(report)
    out = ART / "OS_PROVE_REPORT.json"
    text = json.dumps(report, indent=2) + "\n"
    if "/Users/" in text:
        raise SystemExit("host path leaked into prove report")
    out.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": all(s == DIGITALLY_VALIDATED for s in gates.values()),
                "report": str(out.relative_to(ROOT)),
                "digitally_validated_gates": report["digitally_validated_gates"],
                "tokens": tokens,
            },
            indent=2,
        )
    )
    return 0 if report["digitally_validated_gates"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
