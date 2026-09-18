"""CX2H.4 J4 gap audit + calendar/contacts GUI remediation."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx2g.qemu import screendump
from gunnchos_device_os.cx2g.session import ppm_diff
from gunnchos_device_os.cx2h4 import host_providers as hp
from gunnchos_device_os.cx2h4.session import cdp_eval, provider_api, _ssh


def run_j4_gap_audit(repo: Path, monitor: Path, captures: Path, caldav_prov: Dict[str, Any]) -> Dict[str, Any]:
    """Create calendar event + contact via Chromium GUI against real CalDAV/CardDAV.

    Chat/meeting remain EXTERNAL_PROVIDER_PENDING (GAP CX-P1 Connect chat/video) —
    ordinary-user P0 baseline requires email/calendar path; chat/video are P1.
    """
    captures.mkdir(parents=True, exist_ok=True)
    out: Dict[str, Any] = {
        "schema": "gunnchos.cx2h4.j4_gap_audit.v1",
        "J4_P0_DIGITAL_BLOCKER": True,
    }

    # Prior truth (honest)
    prior_cx2 = repo / "artifacts/complete_experience/cx2/JOURNEYS.json"
    prior_note = {}
    if prior_cx2.is_file():
        try:
            prior_note = json.loads(prior_cx2.read_text()).get("J4") or {}
        except Exception:
            prior_note = {}

    guest_url = caldav_prov.get("guest_url") or f"http://10.0.2.2:{hp.CALDAV_PORT}/"
    before = screendump(monitor, captures / "j4_before_browser.ppm")
    launch = provider_api(repo, "/api/browser/launch", "POST", json.dumps({"url": guest_url}))
    time.sleep(4)
    after = screendump(monitor, captures / "j4_calendar_gui.ppm")
    diff = ppm_diff(
        Path(before["path"]) if before.get("path") else captures / "j4_before_browser.ppm",
        Path(after["path"]) if after.get("path") else captures / "j4_calendar_gui.ppm",
        min_changed_pct=0.2,
    )
    title = cdp_eval(
        repo,
        "document.title",
        port=9334,
    )
    # Click create event + create contact via DOM
    click = cdp_eval(
        repo,
        """
(async () => {
  const status = document.getElementById('status');
  const evBtn = document.getElementById('create-event');
  const ctBtn = document.getElementById('create-contact');
  if (!evBtn || !ctBtn) return {ok:false, error:'missing_buttons', title: document.title};
  evBtn.click();
  await new Promise(r => setTimeout(r, 800));
  ctBtn.click();
  await new Promise(r => setTimeout(r, 800));
  return {
    ok: true,
    title: document.title,
    status: status ? status.textContent : null,
    event: window.__CX2H4_EVENT__ || null,
    contact: window.__CX2H4_CONTACT__ || null
  };
})()
""",
        port=9334,
    )
    time.sleep(1)
    server = hp.verify_server_objects()
    calendar_gui_ok = bool(
        launch.get("ok")
        and (diff.get("ok") or (title.get("result") == "CX2H4 Connect Calendar") or (click.get("result") or {}).get("ok"))
        and server.get("event_ok")
    )
    contacts_gui_ok = bool(server.get("contact_ok") and launch.get("ok"))

    calendar = {
        "provider": "cx2h4_minimal_caldav + Chromium GUI",
        "ui_surface": "Chromium → CalDAV HTML GUI → PUT /caldav/...ics",
        "real_fixture_contract": "real",
        "persistence": bool(server.get("event_ok")),
        "offline_behavior": "local server objects survive provider process restart (filesystem)",
        "user_action_path": "user clicks Create calendar event in browser GUI",
        "evidence_class": "REAL_PROVIDER_GUI_PASS" if calendar_gui_ok else "BLOCKED",
        "ok": calendar_gui_ok,
        "launch": launch,
        "fb_diff": diff,
        "cdp_title": title,
        "cdp_click": click,
        "server": {k: server.get(k) for k in ("event_ok", "event_path", "event_bytes", "http_event_prefix")},
    }
    contacts = {
        "provider": "cx2h4_minimal_carddav + Chromium GUI",
        "ui_surface": "Chromium → CardDAV HTML GUI → PUT /carddav/...vcf",
        "real_fixture_contract": "real",
        "persistence": bool(server.get("contact_ok")),
        "offline_behavior": "local server objects survive provider process restart (filesystem)",
        "user_action_path": "user clicks Create contact in browser GUI",
        "evidence_class": "REAL_PROVIDER_GUI_PASS" if contacts_gui_ok else "BLOCKED",
        "ok": contacts_gui_ok,
        "server": {k: server.get(k) for k in ("contact_ok", "contact_path", "contact_bytes", "http_contact_prefix")},
    }
    chat = {
        "provider": None,
        "ui_surface": None,
        "real_fixture_contract": "external_pending",
        "persistence": False,
        "offline_behavior": "n/a",
        "user_action_path": "none qualified",
        "evidence_class": "EXTERNAL_PROVIDER_PENDING",
        "ok": False,
        "gap_backlog": "CX-P1 Connect chat/video",
        "note": "P1 major — not ordinary-user P0 baseline; do not hide",
    }
    meeting = {
        "provider": None,
        "ui_surface": None,
        "real_fixture_contract": "external_pending",
        "persistence": False,
        "offline_behavior": "n/a",
        "user_action_path": "digital meeting-join entry not productized",
        "evidence_class": "EXTERNAL_PROVIDER_PENDING",
        "HUMAN_AV_QUALITY_PENDING": True,
        "PHYSICAL_CAMERA_MIC_PENDING": True,
        "ok": False,
        "gap_backlog": "CX-P1 Connect chat/video",
        "note": "Physical camera/mic not required for digital join; join path still missing → external/P1",
    }
    collab_share = {
        "provider": None,
        "ui_surface": None,
        "real_fixture_contract": "not_declared_p0",
        "persistence": False,
        "evidence_class": "NOT_APPLICABLE",
        "ok": True,
        "note": "No separate P0 collab/file-sharing product surface declared beyond Vault+mail attachment (J2)",
    }

    # P0 digital blocker: calendar OR contacts missing real GUI
    p0_blocker = not (calendar_gui_ok and contacts_gui_ok)
    j4_class = "BLOCKED"
    if calendar_gui_ok and contacts_gui_ok:
        # Chat/meeting remain external; J4 full journey not DIGITAL_PASS
        j4_class = "REAL_PROVIDER_GUI_PARTIAL"

    out.update(
        {
            "prior_j4": {
                "evidence_class": prior_note.get("evidence_class"),
                "note": "CX2 had CalDAV/CardDAV CLI; GUI missing → CX2H* J4_CLASS=BLOCKED",
            },
            "calendar": calendar,
            "contacts": contacts,
            "chat_messaging": chat,
            "meeting_video_entry": meeting,
            "collaboration_file_sharing": collab_share,
            "J4_P0_DIGITAL_BLOCKER": p0_blocker,
            "J4_CLASS": j4_class,
            "p0_basis": "GUNNCHOS3K ordinary-user baseline + CX-P0-006 email/calendar; chat/video is CX-P1",
            "ok": not p0_blocker,
        }
    )
    return out
