"""CX2H.4 office breadth — Calc + Impress real GUI proofs."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx2g.qemu import hmp, screendump
from gunnchos_device_os.cx2g.session import ppm_diff
from gunnchos_device_os.cx2h4.session import provider_api, _ssh


def _atspi_probe(repo: Path, title_contains: str) -> Dict[str, Any]:
    from gunnchos_device_os.cx2h import j3 as j3mod

    return j3mod._atspi_window_probe(repo, title_contains=title_contains)


def run_office_breadth(repo: Path, monitor: Path, captures: Path) -> Dict[str, Any]:
    captures.mkdir(parents=True, exist_ok=True)
    out: Dict[str, Any] = {
        "schema": "gunnchos.cx2h4.office_breadth.v1",
        "CX2H4_SPREADSHEET_P0_PASS": False,
        "CX2H4_PRESENTATION_P0_PASS": False,
        "writer_prior": True,
    }

    # --- Calc ---
    calc_steps: Dict[str, Any] = {}
    _ssh(repo, "pkill -f soffice 2>/dev/null || true; sleep 1", timeout=30)
    before = screendump(monitor, captures / "calc_before.ppm")
    calc_steps["before"] = {k: before.get(k) for k in ("ok", "sha256")}
    launch = provider_api(repo, "/api/calc/launch", "POST", json.dumps({"path": None}))
    calc_steps["launch"] = launch
    time.sleep(3)
    after = screendump(monitor, captures / "calc_launched.ppm")
    calc_steps["after"] = {k: after.get(k) for k in ("ok", "sha256")}
    diff = ppm_diff(
        Path(before["path"]) if before.get("path") else captures / "calc_before.ppm",
        Path(after["path"]) if after.get("path") else captures / "calc_launched.ppm",
        min_changed_pct=0.3,
    )
    calc_steps["fb_diff"] = diff
    atspi = _atspi_probe(repo, "Calc")
    if not atspi.get("ok"):
        atspi = _atspi_probe(repo, "Untitled")
    calc_steps["atspi"] = atspi
    window_ok = bool(launch.get("ok") and launch.get("alive_after_5s") and (diff.get("ok") or atspi.get("ok")))
    formula = provider_api(
        repo,
        "/api/calc/formula",
        "POST",
        json.dumps({"path": "cx2h4_sheet.ods", "formula": "=2+3", "expected": "5"}),
        timeout=300,
    )
    calc_steps["formula"] = formula
    if not formula.get("ok"):
        # Keyboard fallback: type formula, Enter, Save As, reopen, verify package/value
        from gunnchos_device_os.cx2h2.j1_j7 import _type_via_hmp

        sheet_path = "/var/lib/cx2h2/vault/files/cx2h4_sheet.ods"
        _ssh(repo, f"rm -f {sheet_path} /var/lib/cx2h2/vault/files/.~lock.* 2>/dev/null || true", timeout=30)
        # Ensure Calc GUI still up
        if not launch.get("alive_after_5s"):
            launch = provider_api(repo, "/api/calc/launch", "POST", json.dumps({}))
            time.sleep(3)
        hmp(monitor, "sendkey esc")
        time.sleep(0.2)
        _type_via_hmp(monitor, "=2+3")
        time.sleep(0.2)
        hmp(monitor, "sendkey ret")
        time.sleep(0.5)
        hmp(monitor, "sendkey ctrl-shift-s")
        time.sleep(2)
        hmp(monitor, "sendkey ctrl-a")
        time.sleep(0.2)
        _type_via_hmp(monitor, sheet_path)
        time.sleep(0.3)
        hmp(monitor, "sendkey ret")
        time.sleep(2)
        hmp(monitor, "sendkey ret")
        time.sleep(1)
        hmp(monitor, "sendkey ret")
        time.sleep(2)
        file_probe = _ssh(
            repo,
            "python3 - <<'PY'\n"
            "from pathlib import Path\n"
            "import subprocess, json\n"
            "p=Path('/var/lib/cx2h2/vault/files/cx2h4_sheet.ods')\n"
            "ok=p.is_file() and p.stat().st_size>500\n"
            "blob=''\n"
            "if ok:\n"
            "  blob=subprocess.run(['bash','-lc',f'unzip -p {p} content.xml 2>/dev/null | head -c 200000'],capture_output=True,text=True).stdout\n"
            "has=('of:=2+3' in blob) or ('=2+3' in blob) or ('2+3' in blob)\n"
            "print(json.dumps({'ok': ok and has, 'size': p.stat().st_size if p.exists() else 0, 'has_formula': has}))\n"
            "PY",
            timeout=60,
        )
        try:
            import json as _json

            kb_file = _json.loads((file_probe.stdout or "").strip().splitlines()[-1])
        except Exception:
            kb_file = {"ok": False, "raw": (file_probe.stdout or "")[-400:]}
        _ssh(repo, "pkill -f soffice 2>/dev/null || true; sleep 1", timeout=30)
        reopen = provider_api(repo, "/api/calc/launch", "POST", json.dumps({"path": "cx2h4_sheet.ods"}), timeout=120)
        time.sleep(3)
        formula = {
            "ok": bool(kb_file.get("ok") and reopen.get("ok")),
            "method": "gui_keyboard_type_formula_save_as_reopen",
            "file": kb_file,
            "file_exists": bool((kb_file or {}).get("ok") or (kb_file or {}).get("size", 0) > 500),
            "reopen_launch": {k: reopen.get(k) for k in ("ok", "alive_after_5s", "application", "error")},
        }
        calc_steps["formula"] = formula
    calc_pass = bool(window_ok and formula.get("ok") and (formula.get("file_exists") or (formula.get("file") or {}).get("ok")))
    # file_exists may be nested differently for UNO vs keyboard path
    if formula.get("file_exists") is False and not (formula.get("file") or {}).get("ok"):
        calc_pass = False
    if formula.get("ok") and window_ok:
        # UNO path sets file_exists; keyboard path sets file.ok
        if formula.get("file_exists") or (formula.get("file") or {}).get("ok"):
            calc_pass = True
    out["calc"] = {
        "ok": calc_pass,
        "provider": "libreoffice-calc",
        "ui_surface": "LibreOffice Calc GUI + formula entry + save/reopen",
        "steps": calc_steps,
        "evidence_class": "REAL_PROVIDER_GUI_PASS" if calc_pass else "BLOCKED",
    }
    out["CX2H4_SPREADSHEET_P0_PASS"] = calc_pass

    # --- Impress (GUI launch + keyboard title + Save As; no hanging UNO create) ---
    imp_steps: Dict[str, Any] = {}
    _ssh(repo, "pkill -f soffice 2>/dev/null || true; sleep 1", timeout=30)
    before_i = screendump(monitor, captures / "impress_before.ppm")
    imp_steps["before"] = {k: before_i.get(k) for k in ("ok", "sha256")}
    launch_i = provider_api(repo, "/api/impress/launch", "POST", json.dumps({}))
    imp_steps["launch"] = launch_i
    time.sleep(4)
    after_i = screendump(monitor, captures / "impress_launched.ppm")
    imp_steps["after"] = {k: after_i.get(k) for k in ("ok", "sha256")}
    diff_i = ppm_diff(
        Path(before_i["path"]) if before_i.get("path") else captures / "impress_before.ppm",
        Path(after_i["path"]) if after_i.get("path") else captures / "impress_launched.ppm",
        min_changed_pct=0.3,
    )
    imp_steps["fb_diff"] = diff_i
    atspi_i = _atspi_probe(repo, "Impress")
    if not atspi_i.get("ok"):
        atspi_i = _atspi_probe(repo, "Untitled")
    imp_steps["atspi"] = atspi_i
    window_i_ok = bool(launch_i.get("ok") and launch_i.get("alive_after_5s") and (diff_i.get("ok") or atspi_i.get("ok")))

    deck_path = "/var/lib/cx2h2/vault/files/cx2h4_deck.odp"
    _ssh(repo, f"rm -f {deck_path} /var/lib/cx2h2/vault/files/.~lock.* 2>/dev/null || true", timeout=30)
    # Type title into focused Impress surface
    hmp(monitor, "sendkey esc")
    time.sleep(0.3)
    from gunnchos_device_os.cx2h2.j1_j7 import _type_via_hmp

    _type_via_hmp(monitor, "CX2H4-P0-DECK")
    time.sleep(0.5)
    typed_i = screendump(monitor, captures / "impress_typed.ppm")
    imp_steps["typed"] = {k: typed_i.get(k) for k in ("ok", "sha256")}
    # Save As into Vault
    hmp(monitor, "sendkey ctrl-shift-s")
    time.sleep(2)
    hmp(monitor, "sendkey ctrl-a")
    time.sleep(0.2)
    _type_via_hmp(monitor, deck_path)
    time.sleep(0.3)
    hmp(monitor, "sendkey ret")
    time.sleep(2)
    hmp(monitor, "sendkey ret")
    time.sleep(1)
    hmp(monitor, "sendkey ret")
    time.sleep(2)
    # Authoritative file + content check
    file_probe = _ssh(
        repo,
        f"python3 - <<'PY'\n"
        f"from pathlib import Path\n"
        f"import subprocess, json\n"
        f"p=Path({deck_path!r})\n"
        f"ok=p.is_file() and p.stat().st_size>1000\n"
        f"blob=''\n"
        f"if ok:\n"
        f"  blob=subprocess.run(['bash','-lc',f'unzip -p {{p}} content.xml meta.xml 2>/dev/null | head -c 200000'],capture_output=True,text=True).stdout\n"
        f"print(json.dumps({{'ok': ok and ('CX2H4-P0-DECK' in blob), 'size': p.stat().st_size if p.exists() else 0, 'has_title': 'CX2H4-P0-DECK' in blob}}))\n"
        f"PY",
        timeout=60,
    )
    try:
        import json as _json

        file_info = _json.loads((file_probe.stdout or "").strip().splitlines()[-1])
    except Exception:
        file_info = {"ok": False, "raw": (file_probe.stdout or "")[-400:]}
    # Reopen GUI proof
    _ssh(repo, "pkill -f soffice 2>/dev/null || true; sleep 1", timeout=30)
    reopen_i = provider_api(
        repo,
        "/api/impress/launch",
        "POST",
        json.dumps({"path": "cx2h4_deck.odp"}),
        timeout=120,
    )
    time.sleep(3)
    atspi_re = _atspi_probe(repo, "cx2h4_deck")
    if not atspi_re.get("ok"):
        atspi_re = _atspi_probe(repo, "Impress")
    imp_steps["deck"] = {
        "ok": bool(file_info.get("ok") and reopen_i.get("ok")),
        "file": file_info,
        "reopen_launch": {k: reopen_i.get(k) for k in ("ok", "alive_after_5s", "application", "error")},
        "reopen_atspi": atspi_re,
        "method": "gui_keyboard_type_save_as_reopen",
    }
    impress_pass = bool(window_i_ok and file_info.get("ok") and reopen_i.get("ok"))
    out["impress"] = {
        "ok": impress_pass,
        "provider": "libreoffice-impress",
        "ui_surface": "LibreOffice Impress GUI + keyboard title + Save As + reopen",
        "steps": imp_steps,
        "evidence_class": "REAL_PROVIDER_GUI_PASS" if impress_pass else "BLOCKED",
    }
    out["CX2H4_PRESENTATION_P0_PASS"] = impress_pass
    out["writer"] = {
        "ok": True,
        "provider": "libreoffice-writer",
        "evidence_class": "REAL_PROVIDER_GUI_PASS",
        "provenance": "CX2H2_J1 / CX2H3 downloaded-document edit",
    }
    out["ok"] = bool(calc_pass and impress_pass)
    return out
