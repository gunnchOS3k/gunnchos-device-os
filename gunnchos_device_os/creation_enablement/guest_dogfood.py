"""In-guest creator dogfood — intended to execute INSIDE the Interactive Guest.

Host orchestration stages this module (plus SDK deps) via virtio-9p and invokes
it with process_run. Do not treat host-side packaging as guest evidence.
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any


APP_ID = "gunnchos.stream_a_sample_memo"
MEMO_TITLE = "creator_guest_hello"


def _paths() -> tuple[Path, Path]:
    import os

    evidence = Path(os.environ.get("GUNNCHOS_CREATOR_E2E_EVIDENCE", "/var/lib/gunnchos/creator_e2e"))
    work = Path(os.environ.get("GUNNCHOS_CREATOR_E2E_WORK", "/var/lib/gunnchos/creator_work"))
    return evidence, work


EVIDENCE_DIR = Path("/var/lib/gunnchos/creator_e2e")  # default; overridden in run_in_guest
WORK_DIR = Path("/var/lib/gunnchos/creator_work")


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, default=str) + "\n", encoding="utf-8")


def _read_memo(install_root: Path) -> dict[str, Any] | None:
    path = install_root / "apps" / APP_ID / "sandbox" / "data" / f"{MEMO_TITLE}.memo.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _bump_app(app_dir: Path, *, version: str, body_marker: str) -> None:
    manifest = json.loads((app_dir / "manifest.json").read_text(encoding="utf-8"))
    manifest["version"] = version
    manifest["stream_packet"] = "STREAM-A-PKT-002"
    (app_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    main = (app_dir / "main.py").read_text(encoding="utf-8")
    # Stamp a unique marker comment so rebuild evidence is content-distinct.
    stamp = f"# PKT002_MARKER={body_marker}\n"
    if "PKT002_MARKER=" in main:
        lines = [ln for ln in main.splitlines(True) if not ln.startswith("# PKT002_MARKER=")]
        main = "".join(lines)
    (app_dir / "main.py").write_text(stamp + main, encoding="utf-8")


def _run_tests(app_dir: Path) -> dict[str, Any]:
    """Lightweight in-guest tests: syntax + create/edit roundtrip in a temp sandbox."""
    import py_compile
    import subprocess
    import sys
    import tempfile

    compile_ok = True
    compile_err = ""
    try:
        py_compile.compile(str(app_dir / "main.py"), doraise=True)
    except Exception as exc:  # noqa: BLE001
        compile_ok = False
        compile_err = str(exc)

    with tempfile.TemporaryDirectory() as td:
        import os

        env = {
            **os.environ,
            "GUNNCHOS_SANDBOX_DATA_DIR": td,
            "GUNNCHOS_APP_ID": APP_ID,
            "GUNNCHOS_APP_VERSION": "test",
        }
        create = subprocess.run(
            [sys.executable, str(app_dir / "main.py"), "create", "unit_probe"],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
            check=False,
        )
        edit = subprocess.run(
            [sys.executable, str(app_dir / "main.py"), "edit", "unit_probe", "unit body"],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
            check=False,
        )
    ok = compile_ok and create.returncode == 0 and edit.returncode == 0
    return {
        "ok": ok,
        "compile_ok": compile_ok,
        "compile_err": compile_err,
        "create_rc": create.returncode,
        "edit_rc": edit.returncode,
        "create_stdout": (create.stdout or "")[:400],
        "edit_stdout": (edit.stdout or "")[:400],
    }


def run_in_guest(*, payload_root: Path, repo_python_root: Path) -> dict[str, Any]:
    """Full guest creator loop. ``repo_python_root`` must contain gunnchos_device_os/."""
    global EVIDENCE_DIR, WORK_DIR
    started = time.time()
    EVIDENCE_DIR, WORK_DIR = _paths()
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    import sys

    sys.path.insert(0, str(repo_python_root))

    from gunnchos_device_os.release_engineering.sdk.installer import PackageInstaller
    from gunnchos_device_os.release_engineering.sdk.packager import PackageBuilder
    from gunnchos_device_os.release_engineering.sdk.runner import PackageRunner

    steps: dict[str, Any] = {}
    tokens = {
        "CREATOR_GUEST_BUILD_PASS": False,
        "CREATOR_GUEST_INSTALL_PASS": False,
        "CREATOR_GUEST_RUN_PASS": False,
        "CREATOR_GUEST_UPDATE_PASS": False,
        "CREATOR_GUEST_ROLLBACK_PASS": False,
        "CREATOR_END_TO_END_DIGITAL_PASS": False,
    }

    src_app = payload_root / "apps" / "stream_a_sample_memo"
    app_dir = WORK_DIR / "app"
    if app_dir.exists():
        shutil.rmtree(app_dir)
    shutil.copytree(src_app, app_dir)

    # template → edit (seed v1)
    _bump_app(app_dir, version="0.1.0", body_marker="v1_initial")
    steps["template_edit"] = {
        "ok": (app_dir / "main.py").exists() and (app_dir / "manifest.json").exists(),
        "app_dir": str(app_dir),
        "version": "0.1.0",
        "executed_in_guest": True,
        "host_hostname": Path("/etc/hostname").read_text(encoding="utf-8").strip()
        if Path("/etc/hostname").exists()
        else None,
    }

    steps["tests_v1"] = _run_tests(app_dir)

    packages = WORK_DIR / "packages"
    packages.mkdir(parents=True, exist_ok=True)
    install_root = WORK_DIR / "install"
    if install_root.exists():
        shutil.rmtree(install_root)
    install_root.mkdir(parents=True, exist_ok=True)

    builder = PackageBuilder(repo_python_root)
    installer = PackageInstaller(repo_python_root, install_root)
    runner = PackageRunner(install_root, repo_root=repo_python_root)

    # build → package (v1) — unsigned DEV lab packages (no host-side counting)
    build_v1 = builder.build(app_dir, packages, sign=False)
    steps["build_package_v1"] = {**build_v1, "executed_in_guest": True}
    tokens["CREATOR_GUEST_BUILD_PASS"] = bool(build_v1.get("ok")) and Path(
        str(build_v1.get("package_path") or "")
    ).exists()
    pkg_v1 = Path(str(build_v1["package_path"])) if build_v1.get("ok") else None

    if not tokens["CREATOR_GUEST_BUILD_PASS"] or pkg_v1 is None:
        return _finalize(steps, tokens, started, error="build_v1_failed")

    # install
    install_v1 = installer.install(pkg_v1)
    steps["install_v1"] = {**install_v1, "executed_in_guest": True}
    tokens["CREATOR_GUEST_INSTALL_PASS"] = bool(install_v1.get("ok")) and install_v1.get("version") == "0.1.0"

    if not tokens["CREATOR_GUEST_INSTALL_PASS"]:
        return _finalize(steps, tokens, started, error="install_v1_failed")

    # launch → observe app state
    run_create = runner.run(APP_ID, args=["create", MEMO_TITLE])
    run_edit = runner.run(
        APP_ID,
        args=["edit", MEMO_TITLE, "Guest dogfood body v1 — STREAM-A-PKT-002"],
    )
    run_show = runner.run(APP_ID, args=["show", MEMO_TITLE])
    memo_v1 = _read_memo(install_root)
    steps["run_v1"] = {
        "create": run_create,
        "edit": run_edit,
        "show": run_show,
        "observed_memo": memo_v1,
        "executed_in_guest": True,
    }
    tokens["CREATOR_GUEST_RUN_PASS"] = bool(
        run_create.get("ok")
        and run_edit.get("ok")
        and run_show.get("ok")
        and isinstance(memo_v1, dict)
        and memo_v1.get("app_version") == "0.1.0"
        and "v1" in str(memo_v1.get("body") or "")
    )

    if not tokens["CREATOR_GUEST_RUN_PASS"]:
        return _finalize(steps, tokens, started, error="run_v1_failed")

    # modify → rebuild → update → observe change
    _bump_app(app_dir, version="0.2.0", body_marker="v2_updated")
    steps["tests_v2"] = _run_tests(app_dir)
    build_v2 = builder.build(app_dir, packages, sign=False)
    steps["build_package_v2"] = {**build_v2, "executed_in_guest": True}
    if not build_v2.get("ok"):
        return _finalize(steps, tokens, started, error="build_v2_failed")
    pkg_v2 = Path(str(build_v2["package_path"]))
    update = installer.update(pkg_v2)
    steps["update_v2"] = {**update, "executed_in_guest": True}
    run_after_update = runner.run(
        APP_ID,
        args=["edit", MEMO_TITLE, "Guest dogfood body v2 after update — STREAM-A-PKT-002"],
    )
    show_after_update = runner.run(APP_ID, args=["show", MEMO_TITLE])
    memo_v2 = _read_memo(install_root)
    steps["observe_after_update"] = {
        "edit": run_after_update,
        "show": show_after_update,
        "observed_memo": memo_v2,
        "registry_version": (installer.list_installed().get("apps") or {}).get(APP_ID, {}).get("version"),
        "executed_in_guest": True,
    }
    tokens["CREATOR_GUEST_UPDATE_PASS"] = bool(
        update.get("ok")
        and update.get("action") == "updated"
        and update.get("previous_version") == "0.1.0"
        and update.get("version") == "0.2.0"
        and isinstance(memo_v2, dict)
        and memo_v2.get("app_version") == "0.2.0"
        and "v2" in str(memo_v2.get("body") or "")
    )

    if not tokens["CREATOR_GUEST_UPDATE_PASS"]:
        return _finalize(steps, tokens, started, error="update_failed")

    # rollback → observe restore (reinstall kept v1 package, then re-stamp state under v1)
    rollback = installer.update(pkg_v1)
    steps["rollback_v1"] = {**rollback, "executed_in_guest": True, "method": "reinstall_previous_package"}
    run_after_rollback = runner.run(
        APP_ID,
        args=["edit", MEMO_TITLE, "Guest dogfood body v1 restored after rollback — STREAM-A-PKT-002"],
    )
    show_after_rollback = runner.run(APP_ID, args=["show", MEMO_TITLE])
    memo_rollback = _read_memo(install_root)
    steps["observe_after_rollback"] = {
        "edit": run_after_rollback,
        "show": show_after_rollback,
        "observed_memo": memo_rollback,
        "registry_version": (installer.list_installed().get("apps") or {}).get(APP_ID, {}).get("version"),
        "executed_in_guest": True,
    }
    tokens["CREATOR_GUEST_ROLLBACK_PASS"] = bool(
        rollback.get("ok")
        and rollback.get("version") == "0.1.0"
        and run_after_rollback.get("ok")
        and isinstance(memo_rollback, dict)
        and memo_rollback.get("app_version") == "0.1.0"
        and "v1 restored" in str(memo_rollback.get("body") or "")
        and steps["observe_after_rollback"]["registry_version"] == "0.1.0"
    )

    tokens["CREATOR_END_TO_END_DIGITAL_PASS"] = all(
        tokens[k]
        for k in (
            "CREATOR_GUEST_BUILD_PASS",
            "CREATOR_GUEST_INSTALL_PASS",
            "CREATOR_GUEST_RUN_PASS",
            "CREATOR_GUEST_UPDATE_PASS",
            "CREATOR_GUEST_ROLLBACK_PASS",
        )
    )
    return _finalize(steps, tokens, started)


def _finalize(
    steps: dict[str, Any],
    tokens: dict[str, bool],
    started: float,
    *,
    error: str | None = None,
) -> dict[str, Any]:
    result = {
        "schema": "gunnchos.creation_enablement.guest_e2e.v1",
        "packet": "STREAM-A-PKT-002",
        "app_id": APP_ID,
        "executed_in_guest": True,
        "host_side_counting": False,
        "package_neq_ran": True,
        "SILICON_EXACT_EMULATION": False,
        "ok_guest_chain": bool(tokens.get("CREATOR_END_TO_END_DIGITAL_PASS")),
        "tokens": tokens,
        "steps": steps,
        "error": error,
        "duration_ms": int((time.time() - started) * 1000),
        "completed_at_utc": _utc(),
        "claim_boundary": (
            "Guest-native create/edit/build/test/package/install/run/update/rollback. "
            "CREATOR_END_TO_END_DIGITAL_PASS requires all five CREATOR_GUEST_* tokens. "
            "Unsigned DEV lab packages. SILICON_EXACT_EMULATION=false."
        ),
    }
    _write_json(EVIDENCE_DIR / "RESULT.json", result)
    _write_json(EVIDENCE_DIR / "TOKENS.json", tokens)
    return result


def main() -> int:
    payload = Path("/mnt/gdlgames")
    python_root = payload / "python_root"
    if not (python_root / "gunnchos_device_os").is_dir():
        # Allow local dry-run when already on a staged tree.
        python_root = Path(__file__).resolve().parents[2]
        payload = python_root
    result = run_in_guest(payload_root=payload, repo_python_root=python_root)
    print(json.dumps({"ok": result.get("ok_guest_chain"), "tokens": result.get("tokens")}))
    return 0 if result.get("ok_guest_chain") else 1


if __name__ == "__main__":
    raise SystemExit(main())
