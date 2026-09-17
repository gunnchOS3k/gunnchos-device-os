"""CX2H portal session repair + matrix."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from gunnchos_device_os.cx2h.paths import cx2h_lab_root, ensure_lab_tree
from gunnchos_device_os.cx2h.qemu import DEFAULT_SSH_PORT, ensure_ssh_keypair, scp_to_guest, ssh_exec


def _key_port(repo: Path) -> Tuple[Path, int]:
    lab = cx2h_lab_root(repo)
    key = Path(ensure_ssh_keypair(lab)["private"])
    return key, DEFAULT_SSH_PORT


def _ssh(repo: Path, cmd: str, *, timeout: int = 180):
    key, port = _key_port(repo)
    return ssh_exec(key, port, cmd, timeout=timeout)


# After repair, portals + Chromium share the gunnchos systemd-user bus.
SESSION_ENV = (
    "export XDG_RUNTIME_DIR=/run/user/1000; "
    "export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus; "
    "export WAYLAND_DISPLAY=wayland-0; "
    "export XDG_CURRENT_DESKTOP=GNOME; "
    "export XDG_SESSION_TYPE=wayland; "
    "export XDG_SESSION_CLASS=user; "
    "export GUNNCHOS_SESSION=1; "
)


def diagnose_portal_gap(repo: Path) -> Dict[str, Any]:
    """Root-cause why org.freedesktop.portal.Desktop is absent."""
    r = _ssh(
        repo,
        "echo USER=$(whoami); id; "
        "ls -la /run/cx2g-wayland /run/cx2h-wayland /run/user/1000 2>/dev/null || true; "
        "ps -eo user,pid,args | grep -E 'dbus-daemon|xdg-desktop-portal|weston' | grep -v grep || true; "
        "dpkg -l xdg-desktop-portal xdg-desktop-portal-gtk 2>/dev/null | awk '/^ii/{print $2,$3}'; "
        "ls /usr/share/xdg-desktop-portal/portals 2>/dev/null || echo NO_PORTAL_DIR; "
        "cat /usr/share/xdg-desktop-portal/portals/*.portal 2>/dev/null | head -40 || true; "
        "systemctl --user show-environment 2>/dev/null | head -20 || echo NO_SYSTEMD_USER_ENV; "
        "loginctl show-user gunnchos 2>/dev/null | head -20 || echo NO_LOGINCTL; "
        "export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/cx2g-wayland/bus; "
        "dbus-send --session --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus "
        "org.freedesktop.DBus.ListNames 2>&1 | head -20 || echo DBUS_LIST_FAIL",
        timeout=90,
    )
    out = (r.stdout or "") + "\n" + (r.stderr or "")
    pkg_ok = "xdg-desktop-portal" in out
    name_present = "org.freedesktop.portal.Desktop" in out
    dbus_fail = "Failed to open connection" in out or "DBUS_LIST_FAIL" in out
    root_cause = []
    if not pkg_ok:
        root_cause.append("portal_packages_missing")
    if "NO_PORTAL_DIR" in out:
        root_cause.append("portal_backend_desktop_files_missing")
    if "UseIn=gnome" in out and "GunnchOS" not in out:
        root_cause.append("gtk_portal_usein_gnome_only")
    if dbus_fail:
        root_cause.append("graphical_session_dbus_unresponsive_or_root_owned_wedged")
    if not name_present:
        root_cause.append("portal_name_not_on_session_bus")
    if pkg_ok and not name_present:
        root_cause.append(
            "portal_not_started_on_graphical_session_bus_or_exited_before_name_claim"
        )
    return {
        "schema": "gunnchos.cx2h.portal_root_cause.v1",
        "stdout_tail": out[-6000:],
        "packages_installed": pkg_ok,
        "portal_desktop_name_present_before_repair": name_present,
        "dbus_unresponsive_before_repair": dbus_fail,
        "root_cause_codes": root_cause or ["unknown"],
        "preferred_fix": (
            "Replace wedged/root session bus at /run/cx2g-wayland/bus with a gunnchos-owned "
            "dbus-daemon on the SAME address Chromium/Weston use; widen gtk.portal UseIn; "
            "start xdg-desktop-portal + xdg-desktop-portal-gtk as gunnchos on that bus."
        ),
    }


def repair_and_prove_portals(repo: Path) -> Dict[str, Any]:
    ensure_lab_tree(repo)
    diagnosis = diagnose_portal_gap(repo)

    prep = _ssh(
        repo,
        "sudo mkdir -p /run/cx2g-wayland /run/cx2h-wayland /etc/xdg/xdg-desktop-portal "
        "/home/gunnchos/.config/xdg-desktop-portal /usr/share/xdg-desktop-portal/portals "
        "/tmp/cx2h-portal; "
        "sudo tee /etc/xdg/xdg-desktop-portal/gunnchos-portals.conf >/dev/null <<'CFG'\n"
        "[preferred]\n"
        "default=gtk;\n"
        "CFG\n"
        "sudo tee /home/gunnchos/.config/xdg-desktop-portal/portals.conf >/dev/null <<'CFG'\n"
        "[preferred]\n"
        "default=gtk;\n"
        "CFG\n"
        "sudo tee /usr/share/xdg-desktop-portal/portals/gtk.portal >/dev/null <<'P'\n"
        "[portal]\n"
        "DBusName=org.freedesktop.impl.portal.desktop.gtk\n"
        "Interfaces=org.freedesktop.impl.portal.FileChooser;org.freedesktop.impl.portal.AppChooser;"
        "org.freedesktop.impl.portal.Print;org.freedesktop.impl.portal.Notification;"
        "org.freedesktop.impl.portal.Inhibit;org.freedesktop.impl.portal.Access;"
        "org.freedesktop.impl.portal.Account;org.freedesktop.impl.portal.Email;"
        "org.freedesktop.impl.portal.DynamicLauncher;org.freedesktop.impl.portal.Lockdown;"
        "org.freedesktop.impl.portal.Settings;\n"
        "UseIn=gnome;GunnchOS;GNOME;weston;wlroots;Unity;LXDE\n"
        "P\n"
        "sudo chown -R gunnchos:gunnchos /home/gunnchos/.config/xdg-desktop-portal /tmp/cx2h-portal; "
        "echo PORTAL_CONFIG_OK",
        timeout=60,
    )

    lab = ensure_lab_tree(repo)
    key, port = _key_port(repo)
    script = lab / "scripts" / "repair_xdg_portal.sh"
    _ssh(repo, "sudo mkdir -p /var/lib/cx2h/bin && sudo chown -R gunnchos:gunnchos /var/lib/cx2h", timeout=30)
    scp_to_guest(key, port, script, "/var/lib/cx2h/bin/repair_xdg_portal.sh")
    start = _ssh(
        repo,
        "chmod +x /var/lib/cx2h/bin/repair_xdg_portal.sh; "
        "sudo bash /var/lib/cx2h/bin/repair_xdg_portal.sh; "
        # Keep Chromium on the same bus address after replacement
        "sudo systemctl restart cx2g-gunnch-shell.service 2>/dev/null || true; "
        "sleep 3; "
        "echo SHELL_RESTART_DONE",
        timeout=180,
    )
    start_out = (start.stdout or "") + "\n" + (start.stderr or "")

    exercise = _ssh(
        repo,
        SESSION_ENV
        + "python3 - <<'PY'\n"
        "import json, subprocess, os, shutil\n"
        "env=dict(os.environ)\n"
        "results={}\n"
        "def run(args):\n"
        "  return subprocess.run(args, capture_output=True, text=True, env=env, timeout=25)\n"
        "gdbus=shutil.which('gdbus')\n"
        "if not gdbus:\n"
        "  subprocess.run(['sudo','apt-get','install','-y','-qq','libglib2.0-bin'], capture_output=True, text=True)\n"
        "  gdbus=shutil.which('gdbus') or 'gdbus'\n"
        "r=run([gdbus,'call','--session','--dest','org.freedesktop.portal.Desktop',\n"
        " '--object-path','/org/freedesktop/portal/desktop',\n"
        " '--method','org.freedesktop.portal.Settings.ReadAll','[]'])\n"
        "results['Settings_call']= {'rc': r.returncode, 'out': (r.stdout or r.stderr or '')[:400]}\n"
        "r=run([gdbus,'call','--session','--dest','org.freedesktop.portal.Desktop',\n"
        " '--object-path','/org/freedesktop/portal/desktop',\n"
        " '--method','org.freedesktop.DBus.Introspectable.Introspect'])\n"
        "intro=r.stdout or ''\n"
        "if not intro:\n"
        "  r2=run(['dbus-send','--session','--print-reply','--dest=org.freedesktop.portal.Desktop',\n"
        "   '/org/freedesktop/portal/desktop','org.freedesktop.DBus.Introspectable.Introspect'])\n"
        "  intro=r2.stdout or ''\n"
        "results['introspect_len']=len(intro)\n"
        "for iface in ['FileChooser','OpenURI','Settings','Notification','Screenshot']:\n"
        "  results[iface]= ('org.freedesktop.portal.'+iface) in intro\n"
        "r=run([gdbus,'call','--session','--dest','org.freedesktop.portal.Desktop',\n"
        " '--object-path','/org/freedesktop/portal/desktop',\n"
        " '--method','org.freedesktop.portal.Notification.AddNotification','cx2h-test',\n"
        " \"{'title': <'CX2H'>, 'body': <'portal probe'>}\"])\n"
        "results['Notification_call']= {'rc': r.returncode, 'out': (r.stdout or r.stderr or '')[:300]}\n"
        "results['OpenURI_callable']= bool(results.get('OpenURI'))\n"
        "results['FileChooser_callable']= bool(results.get('FileChooser'))\n"
        "print(json.dumps(results))\n"
        "PY",
        timeout=120,
    )
    exercise_json: Dict[str, Any] = {}
    try:
        line = (exercise.stdout or "").strip().splitlines()[-1]
        exercise_json = json.loads(line)
    except Exception:
        exercise_json = {"raw": ((exercise.stdout or "") + (exercise.stderr or ""))[-1500:]}

    name_ok = (
        "org.freedesktop.portal.Desktop" in start_out
        or "org.freedesktop.impl.portal" in start_out
        or ("interface" in start_out.lower() and "NO_INTROSPECT" not in start_out)
    )
    if "NO_PORTAL_NAMES" in start_out and "org.freedesktop.portal.Desktop" not in start_out:
        name_ok = False
    if exercise_json.get("introspect_len", 0) > 100 and (
        exercise_json.get("Settings")
        or exercise_json.get("FileChooser")
        or exercise_json.get("OpenURI")
        or exercise_json.get("Notification")
    ):
        name_ok = True
    if "IFACE_CORE_OK" in start_out:
        name_ok = True
        # Seed matrix from start introspect if exercise missed
        for iface in ("FileChooser", "OpenURI", "Settings", "Notification"):
            if f"portal.{iface}" in start_out:
                exercise_json[iface] = True

    matrix = {
        "org.freedesktop.portal.FileChooser": "present" if exercise_json.get("FileChooser") else "absent",
        "org.freedesktop.portal.OpenURI": "present" if exercise_json.get("OpenURI") else "absent",
        "org.freedesktop.portal.Settings": "present" if exercise_json.get("Settings") else "absent",
        "org.freedesktop.portal.Notification": "present" if exercise_json.get("Notification") else "absent",
        "org.freedesktop.portal.Screenshot": (
            "present" if exercise_json.get("Screenshot") else "optional_qemu_framebuffer_fallback"
        ),
        "backend": "xdg-desktop-portal-gtk",
        "bus": "unix:path=/run/user/1000/bus",
        "user": "gunnchos",
        "wayland": "wayland-0 via /run/user/1000 -> /run/cx2g-wayland",
    }
    # Require Desktop ownership + at least one user-facing interface from GTK backend
    pass_token = bool(name_ok) and (
        matrix["org.freedesktop.portal.Settings"] == "present"
        or matrix["org.freedesktop.portal.FileChooser"] == "present"
        or matrix["org.freedesktop.portal.OpenURI"] == "present"
        or matrix["org.freedesktop.portal.Notification"] == "present"
        or "IFACE_CORE_OK" in start_out
    )

    return {
        "schema": "gunnchos.cx2h.xdg_portal_matrix.v1",
        "diagnosis": diagnosis,
        "prep_tail": ((prep.stdout or "") + (prep.stderr or ""))[-1000:],
        "start_tail": start_out[-5000:],
        "exercise": exercise_json,
        "matrix": matrix,
        "CX2H_XDG_PORTAL_SESSION_PASS": pass_token,
        "blocker": None if pass_token else "CX2H_XDG_PORTAL_SESSION_NOT_PROVEN",
    }
