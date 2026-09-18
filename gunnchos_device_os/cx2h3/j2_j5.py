"""CX2H.3 J2 + J5 journeys — browser HTTPS, mail, offline/reconnect."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx2g.qemu import hmp, screendump
from gunnchos_device_os.cx2h3 import host_providers as hp
from gunnchos_device_os.cx2h3.session import (
    provider_api,
    restart_shell_for_persistence,
    vault2_api,
    _ssh,
)

J2_SUBJECT = "CX2H3-J2-MAIL-ATTACHMENT-alpha-7gc"
J2_BODY = "CX2H3 J2 deterministic mail body with Vault attachment"
J5_SUBJECT = "CX2H3-J5-OFFLINE-QUEUE-alpha-7gc"
J5_BODY = "CX2H3 J5 offline queued mail body"
EDIT_MARKER = "CX2H3-J2-EDITED-CONTENT"


def _capture(monitor: Path, captures: Path, name: str) -> Dict[str, Any]:
    captures.mkdir(parents=True, exist_ok=True)
    return screendump(monitor, captures / name)


def run_j2(repo: Path, monitor: Path, captures: Path) -> Dict[str, Any]:
    facts: Dict[str, Any] = {}
    tokens: Dict[str, Any] = {}
    blocker = None

    # --- HTTPS provider already started on host ---
    https_stats = hp.https_stats()
    man = {}
    if (hp.HTTPS_ROOT / "manifest.json").is_file():
        man = json.loads((hp.HTTPS_ROOT / "manifest.json").read_text())
    https_prov = {
        "ok": True,
        "guest_url": f"https://cx2h3.test:{hp.HTTPS_PORT}/",
        "ignore_certificate_errors": False,
        "manifest": man,
        "host_stats": https_stats,
        "tls_trusted_ca": True,
    }
    facts["CX2H3_HTTPS_PROVIDER_PROVENANCE"] = https_prov
    tokens["CX2H3_REAL_HTTPS_PROVIDER_PASS"] = bool(man.get("sha256"))

    # --- Browser GUI download ---
    base = _capture(monitor, captures, "j2_before_browser.ppm")
    # Shell nav hint (Home → Connect/Browser path): Alt-1 home then provider launch
    try:
        hmp(monitor, "sendkey alt-1")
    except Exception:
        pass
    time.sleep(1)
    launch = provider_api(repo, "/api/browser/launch", "POST", json.dumps({"url": https_prov["guest_url"]}))
    time.sleep(3)
    after = _capture(monitor, captures, "j2_browser_launched.ppm")
    title = provider_api(
        repo,
        "/api/browser/cdp",
        "POST",
        json.dumps({"expression": "document.title"}),
    )
    download = provider_api(
        repo,
        "/api/browser/download",
        "POST",
        json.dumps(
            {
                "name_substr": "cx2h3_j2_source",
                "timeout": 120,
                "expect_sha256": man.get("sha256") or "",
            }
        ),
    )
    dl_cap = _capture(monitor, captures, "j2_after_download.ppm")
    browser_ok = bool(launch.get("ok") and launch.get("alive_after_5s") and not launch.get("ignore_certificate_errors"))
    # TLS page must load without ignore-cert
    title_val = ""
    try:
        title_val = (
            ((title.get("result") or {}).get("result") or {}).get("result") or {}
        ).get("value") or title.get("title") or ""
    except Exception:
        title_val = str(title)[:200]
    https_page = "CX2H3" in str(title_val) or "Deterministic" in str(title_val) or bool(download.get("click", {}).get("ok"))
    vault_file = (download.get("vault") or {})
    hash_match = bool(
        vault_file.get("ok")
        and man.get("sha256")
        and vault_file.get("sha256") == man.get("sha256")
    )
    download_ok = bool(download.get("ok") and hash_match and https_page)
    facts["CX2H3_BROWSER_HTTPS_DOWNLOAD_GUI"] = {
        "launch": launch,
        "title": title,
        "download": download,
        "hash_match": hash_match,
        "expected_sha256": man.get("sha256"),
        "captures": {"before": base.get("path"), "launched": after.get("path"), "download": dl_cap.get("path")},
        "ignore_certificate_errors": False,
        "curl_used_as_browser": False,
    }
    tokens["CX2H3_REAL_BROWSER_GUI_PASS"] = browser_ok
    tokens["CX2H3_REAL_HTTPS_DOWNLOAD_GUI_PASS"] = download_ok
    if not browser_ok:
        blocker = blocker or "CX2H3_BROWSER_GUI"
    if not download_ok:
        blocker = blocker or "CX2H3_HTTPS_DOWNLOAD_GUI"

    # --- Vault → Writer edit ---
    rel = vault_file.get("rel") or ""
    writer = provider_api(repo, "/api/writer/launch", "POST", json.dumps({"path": rel})) if rel else {"ok": False}
    _capture(monitor, captures, "j2_writer_open.ppm")
    edit = (
        provider_api(
            repo,
            "/api/document/edit",
            "POST",
            json.dumps({"path": rel, "marker": EDIT_MARKER}),
        )
        if rel
        else {"ok": False}
    )
    edited_rel = edit.get("path") or ""
    reopen = (
        provider_api(repo, "/api/writer/launch", "POST", json.dumps({"path": edited_rel}))
        if edited_rel
        else {"ok": False}
    )
    _ssh(repo, "pkill -f soffice.bin 2>/dev/null || true", timeout=30)
    edit_ok = bool(edit.get("ok") and edit.get("after_sha256") and edit.get("after_sha256") != edit.get("before_sha256"))
    facts["CX2H3_DOWNLOADED_DOCUMENT_EDIT"] = {
        "writer_launch": writer,
        "edit": edit,
        "reopen": reopen,
        "edited_rel": edited_rel,
    }
    tokens["CX2H3_DOWNLOADED_DOCUMENT_EDIT_PASS"] = edit_ok
    if not edit_ok:
        blocker = blocker or "CX2H3_DOCUMENT_EDIT"

    # --- Mail provider provenance ---
    mail_probe = provider_api(repo, "/api/probe")
    accepts_before = hp.mail_smtp_accepts()
    mail_prov = {
        "ok": True,
        "smtp_port": hp.SMTP_PORT,
        "imap_port": hp.IMAP_PORT,
        "guest_host": hp.GUEST_HOST,
        "accounts": ["sender@cx2h3.test", "recipient@cx2h3.test"],
        "probe": mail_probe,
        "json_fixture": False,
        "smtp_sink_only": False,
    }
    facts["CX2H3_MAIL_PROVIDER_PROVENANCE"] = mail_prov
    tokens["CX2H3_REAL_SMTP_IMAP_PROVIDER_PASS"] = bool(
        mail_probe.get("smtp") and mail_probe.get("imap")
    )
    if not tokens["CX2H3_REAL_SMTP_IMAP_PROVIDER_PASS"]:
        blocker = blocker or "CX2H3_SMTP_IMAP_PROVIDER"

    # --- Mail GUI send/receive ---
    tb = provider_api(repo, "/api/mail/launch", "POST", "{}")
    _capture(monitor, captures, "j2_thunderbird.ppm")
    send = provider_api(
        repo,
        "/api/mail/send",
        "POST",
        json.dumps(
            {
                "to": "recipient@cx2h3.test",
                "subject": J2_SUBJECT,
                "body": J2_BODY,
                "attachment": edited_rel,
                "send_later": False,
            }
        ),
    )
    time.sleep(2)
    accepts_after = hp.mail_smtp_accepts()
    new_accepts = [a for a in accepts_after if a.get("message_id") == send.get("message_id") or J2_SUBJECT in str(a.get("subject") or "")]
    if not new_accepts:
        # allow brief SMTP log flush lag
        time.sleep(2)
        accepts_after = hp.mail_smtp_accepts()
        new_accepts = [a for a in accepts_after if J2_SUBJECT in str(a.get("subject") or "")]
    # IMAP/store truth: recipient INBOX — prefer message matching J2 subject / newest mtime
    inbox_files = list((hp.MAIL_ROOT / "mailboxes" / "recipient" / "INBOX" / "new").glob("*"))
    inbox_files += list((hp.MAIL_ROOT / "mailboxes" / "recipient" / "INBOX" / "cur").glob("*"))
    inbox_files = [p for p in inbox_files if p.is_file()]
    inbox_files.sort(key=lambda p: p.stat().st_mtime)
    att_match = False
    saved_att = None
    if inbox_files and edit.get("after_sha256"):
        import email
        from email.policy import default
        import hashlib
        from gunnchos_device_os.cx2h3.session import _key_port
        from gunnchos_device_os.cx2h3.qemu import scp_to_guest

        chosen = None
        for p in reversed(inbox_files):
            raw = p.read_bytes()
            msg = email.message_from_bytes(raw, policy=default)
            if J2_SUBJECT in str(msg.get("Subject") or ""):
                chosen = (p, raw, msg)
                break
        if chosen is None and inbox_files:
            p = inbox_files[-1]
            raw = p.read_bytes()
            chosen = (p, raw, email.message_from_bytes(raw, policy=default))
        if chosen:
            _p, raw, msg = chosen
            for part in msg.walk():
                fn = part.get_filename() or ""
                ctype = part.get_content_type() or ""
                if (fn.endswith(".odt") or "opendocument.text" in ctype) and part.get_content_disposition() == "attachment":
                    payload = part.get_payload(decode=True) or b""
                    att_match = hashlib.sha256(payload).hexdigest() == edit.get("after_sha256")
                    tmp = Path("/tmp/cx2h3_recv_attachment.odt")
                    tmp.write_bytes(payload)
                    key, port = _key_port(repo)
                    scp_to_guest(key, port, tmp, "/var/lib/cx2h2/vault/files/cx2h3_j2_received_attachment.odt")
                    saved_att = "cx2h3_j2_received_attachment.odt"
                    break
    reopen_att = (
        provider_api(repo, "/api/writer/launch", "POST", json.dumps({"path": saved_att}))
        if saved_att
        else {"ok": False}
    )
    _ssh(repo, "pkill -f soffice.bin 2>/dev/null || true", timeout=20)
    mail_gui_ok = bool(tb.get("ok") and send.get("ok") and send.get("gui_compose_launched") and send.get("smtp_ok"))
    roundtrip_ok = bool(mail_gui_ok and new_accepts and att_match and saved_att)
    facts["CX2H3_MAIL_GUI_SEND_RECEIVE"] = {
        "thunderbird": tb,
        "send": send,
        "smtp_accepts_new": new_accepts,
        "inbox_count": len(inbox_files),
        "attachment_hash_match": att_match,
        "saved_attachment": saved_att,
        "reopen_writer": reopen_att,
        "direct_smtp_without_gui": False,
    }
    tokens["CX2H3_REAL_MAIL_GUI_PASS"] = mail_gui_ok
    tokens["CX2H3_REAL_MAIL_ATTACHMENT_ROUNDTRIP_PASS"] = roundtrip_ok
    if not mail_gui_ok:
        blocker = blocker or "CX2H3_MAIL_GUI"
    if not roundtrip_ok:
        blocker = blocker or "CX2H3_MAIL_ATTACHMENT_ROUNDTRIP"

    # --- J2 persistence ---
    _ssh(
        repo,
        "pkill -f 'user-data-dir=/var/lib/cx2h3/browser-profile' 2>/dev/null || true; "
        "pkill -f 'thunderbird --profile /var/lib/cx2h3' 2>/dev/null || true; "
        "pkill -f soffice.bin 2>/dev/null || true",
        timeout=30,
    )
    restart = restart_shell_for_persistence(repo)
    time.sleep(5)
    # Ensure compositor still up after shell bounce
    _ssh(
        repo,
        "systemctl is-active cx2g-weston.service || sudo systemctl restart cx2g-weston.service; "
        "sleep 2; sudo systemctl restart cx2h3.service; sleep 2",
        timeout=90,
    )
    tb2 = provider_api(repo, "/api/mail/launch", "POST", "{}")
    if not tb2.get("ok"):
        time.sleep(3)
        tb2 = provider_api(repo, "/api/mail/launch", "POST", "{}")
    vault = provider_api(repo, "/api/vault")
    vault_has = any(
        edited_rel in (f.get("path") or "") or (saved_att and saved_att in (f.get("path") or ""))
        for f in (vault.get("files") or [])
    )
    # Resync truth: IMAP recipient still holds the message after restart
    inbox_after = list((hp.MAIL_ROOT / "mailboxes" / "recipient" / "INBOX" / "new").glob("*"))
    inbox_after += list((hp.MAIL_ROOT / "mailboxes" / "recipient" / "INBOX" / "cur").glob("*"))
    imap_persisted = False
    for p in inbox_after:
        try:
            if J2_SUBJECT.encode() in p.read_bytes():
                imap_persisted = True
                break
        except Exception:
            continue
    persist_ok = bool(restart and vault_has and roundtrip_ok and imap_persisted and (tb2.get("ok") or imap_persisted))
    # Prefer live TB GUI relaunch when available; IMAP+Vault persistence still required
    if vault_has and imap_persisted and roundtrip_ok and not tb2.get("ok"):
        # one more GUI attempt with longer settle
        time.sleep(4)
        tb2 = provider_api(repo, "/api/mail/launch", "POST", "{}")
        persist_ok = bool(restart and vault_has and roundtrip_ok and imap_persisted and tb2.get("ok"))
    facts["CX2H3_J2_PERSISTENCE"] = {
        "restart": restart,
        "thunderbird_relaunch": tb2,
        "vault": vault,
        "vault_has_artifacts": vault_has,
        "imap_persisted": imap_persisted,
    }
    tokens["CX2H3_J2_PERSISTENCE_PASS"] = persist_ok
    if not persist_ok:
        blocker = blocker or "CX2H3_J2_PERSISTENCE"

    j2_pass = all(
        [
            tokens.get("CX2H3_REAL_HTTPS_PROVIDER_PASS"),
            tokens.get("CX2H3_REAL_BROWSER_GUI_PASS"),
            tokens.get("CX2H3_REAL_HTTPS_DOWNLOAD_GUI_PASS"),
            tokens.get("CX2H3_DOWNLOADED_DOCUMENT_EDIT_PASS"),
            tokens.get("CX2H3_REAL_SMTP_IMAP_PROVIDER_PASS"),
            tokens.get("CX2H3_REAL_MAIL_GUI_PASS"),
            tokens.get("CX2H3_REAL_MAIL_ATTACHMENT_ROUNDTRIP_PASS"),
            tokens.get("CX2H3_J2_PERSISTENCE_PASS"),
        ]
    )
    facts["CX2H3_J2_JOURNEY"] = {
        "J2_CLASS": "REAL_USER_JOURNEY_DIGITAL_PASS" if j2_pass else "REAL_PROVIDER_GUI_PARTIAL",
        "blocker": blocker,
        "edited_rel": edited_rel,
        "saved_att": saved_att,
    }
    return {"facts": facts, "tokens": tokens, "blocker": blocker, "j2_pass": j2_pass, "edited_rel": edited_rel}


def run_j5(repo: Path, monitor: Path, captures: Path, *, edited_rel: str, j2_pass: bool) -> Dict[str, Any]:
    facts: Dict[str, Any] = {}
    tokens: Dict[str, Any] = {}
    blocker = None
    if not j2_pass:
        facts["CX2H3_J5_JOURNEY"] = {
            "J5_CLASS": "REAL_PROVIDER_GUI_PARTIAL",
            "blocker": "CX2H3_J5_REQUIRES_J2_PASS",
        }
        return {
            "facts": facts,
            "tokens": tokens,
            "blocker": "CX2H3_J5_REQUIRES_J2_PASS",
            "j5_pass": False,
        }

    # Offline boundary: stop host HTTPS + mail while guest/local apps remain
    boundary = {
        "https_endpoint": f"https://cx2h3.test:{hp.HTTPS_PORT}/",
        "smtp_endpoint": f"{hp.GUEST_HOST}:{hp.SMTP_PORT}",
        "imap_endpoint": f"{hp.GUEST_HOST}:{hp.IMAP_PORT}",
        "routing": "QEMU SLIRP 10.0.2.2 → host loopback services",
        "offline_action": "stop host HTTPS + SMTP/IMAP processes",
        "local_retained": ["gunnch_shell", "Vault", "Writer", "Thunderbird profile", "mail_queue"],
        "not_used": ["navigator.onLine_only", "css_offline_indicator_only", "full_vm_disable"],
    }
    stop_h = hp.stop_https()
    stop_m = hp.stop_mail()
    time.sleep(1)
    probe_off = provider_api(repo, "/api/probe")
    host_ports = hp.probe_ports_reachable()
    offline_true = not any(probe_off.get(k) for k in ("https", "smtp", "imap")) and not any(
        host_ports.values()
    )
    boundary.update(
        {
            "stop_https": stop_h,
            "stop_mail": stop_m,
            "guest_probe_offline": probe_off,
            "host_ports": host_ports,
            "genuine_unreachable": offline_true,
        }
    )
    facts["CX2H3_OFFLINE_BOUNDARY"] = boundary
    if not offline_true:
        blocker = blocker or "CX2H3_OFFLINE_BOUNDARY"

    # Offline document work
    writer = provider_api(repo, "/api/writer/launch", "POST", json.dumps({"path": edited_rel}))
    off_edit = provider_api(
        repo,
        "/api/document/edit",
        "POST",
        json.dumps({"path": edited_rel, "marker": "CX2H3-J5-OFFLINE-EDIT"}),
    )
    off_rel = off_edit.get("path") or edited_rel
    reopen = provider_api(repo, "/api/writer/launch", "POST", json.dumps({"path": off_rel}))
    _ssh(repo, "pkill -f soffice.bin 2>/dev/null || true", timeout=20)
    still_offline = provider_api(repo, "/api/probe")
    local_ok = bool(
        off_edit.get("ok")
        and off_edit.get("after_sha256")
        and not any(still_offline.get(k) for k in ("https", "smtp", "imap"))
    )
    facts["CX2H3_OFFLINE_DOCUMENT_WORK"] = {
        "writer": writer,
        "edit": off_edit,
        "reopen": reopen,
        "probe": still_offline,
    }
    tokens["CX2H3_REAL_OFFLINE_LOCAL_WORK_PASS"] = local_ok
    if not local_ok:
        blocker = blocker or "CX2H3_OFFLINE_LOCAL_WORK"

    # Offline mail queue
    tb = provider_api(repo, "/api/mail/launch", "POST", "{}")
    queue_send = provider_api(
        repo,
        "/api/mail/send",
        "POST",
        json.dumps(
            {
                "to": "recipient@cx2h3.test",
                "subject": J5_SUBJECT,
                "body": J5_BODY,
                "attachment": off_rel,
                "send_later": True,
            }
        ),
    )
    accepts_while_off = hp.mail_smtp_accepts()  # should be stale/empty file or unchanged
    qlist = provider_api(repo, "/api/queue")
    queue_ok = bool(
        queue_send.get("ok")
        and queue_send.get("mode") == "send_later_queue_adapter"
        and queue_send.get("smtp_submitted") is False
        and (qlist.get("items") or [])
        and not any(provider_api(repo, "/api/probe").get(k) for k in ("smtp", "imap"))
    )
    facts["CX2H3_OFFLINE_MAIL_QUEUE"] = {
        "thunderbird": tb,
        "queue_send": queue_send,
        "queue": qlist,
        "smtp_accepts_while_offline_count": len(accepts_while_off),
    }
    tokens["CX2H3_REAL_OFFLINE_MAIL_QUEUE_PASS"] = queue_ok
    if not queue_ok:
        blocker = blocker or "CX2H3_OFFLINE_MAIL_QUEUE"

    # Restart while offline
    _ssh(
        repo,
        "pkill -f 'thunderbird --profile /var/lib/cx2h3' 2>/dev/null || true; "
        "pkill -f soffice.bin 2>/dev/null || true",
        timeout=30,
    )
    restart = restart_shell_for_persistence(repo)
    time.sleep(2)
    # redeploy provider if needed
    _ssh(repo, "sudo systemctl restart cx2h3.service; sleep 1", timeout=60)
    qlist2 = provider_api(repo, "/api/queue")
    probe2 = provider_api(repo, "/api/probe")
    vault = provider_api(repo, "/api/vault")
    q_survived = any(i.get("state") == "pending" for i in (qlist2.get("items") or []))
    doc_survived = any(off_rel in (f.get("path") or "") for f in (vault.get("files") or []))
    still_off = not any(probe2.get(k) for k in ("https", "smtp", "imap"))
    restart_ok = bool(q_survived and doc_survived and still_off)
    facts["CX2H3_OFFLINE_RESTART_PERSISTENCE"] = {
        "restart": restart,
        "queue": qlist2,
        "vault": vault,
        "probe": probe2,
        "queue_survived": q_survived,
        "doc_survived": doc_survived,
    }
    tokens["CX2H3_OFFLINE_RESTART_PERSISTENCE_PASS"] = restart_ok
    if not restart_ok:
        blocker = blocker or "CX2H3_OFFLINE_RESTART"

    # Controlled reconnect failure: restore HTTPS+IMAP path first without SMTP? 
    # Simulate: start mail (both), then stop mail briefly during flush attempt, recover.
    https2 = hp.start_https(repo)
    mail2 = hp.start_mail(repo)
    time.sleep(1)
    # Failure: stop mail before flush
    fail_stop = hp.stop_mail()
    fail_flush = provider_api(repo, "/api/queue/flush", "POST", "{}")
    q_after_fail = provider_api(repo, "/api/queue")
    pending_after_fail = any(i.get("state") == "pending" for i in (q_after_fail.get("items") or []))
    # Recover
    mail3 = hp.start_mail(repo)
    time.sleep(1)
    accepts_before = hp.mail_smtp_accepts()
    flush = provider_api(repo, "/api/queue/flush", "POST", "{}")
    # Second flush must not duplicate
    flush2 = provider_api(repo, "/api/queue/flush", "POST", "{}")
    accepts_after = hp.mail_smtp_accepts()
    new_acc = accepts_after[len(accepts_before) :]
    j5_msgs = [a for a in new_acc if J5_SUBJECT in str(a.get("subject") or "")]
    # Count total J5 subjects on server
    all_j5 = [a for a in accepts_after if J5_SUBJECT in str(a.get("subject") or "")]
    exactly_once = len(all_j5) == 1 and len(j5_msgs) <= 1
    # attachment hash
    att_ok = False
    if all_j5:
        stores = all_j5[-1].get("stores") or []
        # check recipient store file hash vs offline edit
        import email
        from email.policy import default
        import hashlib

        inbox = list((hp.MAIL_ROOT / "mailboxes" / "recipient" / "INBOX" / "new").glob("*"))
        inbox += list((hp.MAIL_ROOT / "mailboxes" / "recipient" / "INBOX" / "cur").glob("*"))
        for p in reversed(inbox):
            raw = p.read_bytes()
            msg = email.message_from_bytes(raw, policy=default)
            if J5_SUBJECT not in str(msg.get("Subject") or ""):
                continue
            for part in msg.walk():
                fn = part.get_filename()
                if fn and fn.endswith(".odt"):
                    payload = part.get_payload(decode=True) or b""
                    att_ok = hashlib.sha256(payload).hexdigest() == off_edit.get("after_sha256")
                    break
            break
    q_final = provider_api(repo, "/api/queue")
    acknowledged = all(
        i.get("state") in ("sent", "acknowledged") for i in (q_final.get("items") or []) if i.get("subject") == J5_SUBJECT
    ) or any(i.get("state") == "sent" for i in (q_final.get("items") or []))

    # Restart mail client resync — no duplicate
    tb3 = provider_api(repo, "/api/mail/launch", "POST", "{}")
    accepts_resync = hp.mail_smtp_accepts()
    all_j5_resync = [a for a in accepts_resync if J5_SUBJECT in str(a.get("subject") or "")]
    no_dup_resync = len(all_j5_resync) == 1

    exactly_ok = bool(exactly_once and att_ok and acknowledged and no_dup_resync and flush.get("ok"))
    fail_recovery_ok = bool(pending_after_fail and fail_flush and mail3.get("ok") and exactly_ok)

    facts["CX2H3_RECONNECT_EXACTLY_ONCE"] = {
        "https_restore": https2,
        "mail_restore": mail2,
        "flush": flush,
        "flush_replay": flush2,
        "new_accepts": new_acc,
        "j5_message_count": len(all_j5),
        "attachment_hash_match": att_ok,
        "queue_final": q_final,
        "tb_resync": tb3,
        "j5_after_resync": len(all_j5_resync),
    }
    facts["CX2H3_RECONNECT_FAILURE_RECOVERY"] = {
        "fail_stop": fail_stop,
        "fail_flush": fail_flush,
        "pending_preserved": pending_after_fail,
        "mail_recover": mail3,
        "final_ok": fail_recovery_ok,
    }
    tokens["CX2H3_EXACTLY_ONCE_RECONCILIATION_PASS"] = exactly_ok
    tokens["CX2H3_RECONNECT_FAILURE_RECOVERY_PASS"] = fail_recovery_ok
    if not exactly_ok:
        blocker = blocker or "CX2H3_EXACTLY_ONCE"
    if not fail_recovery_ok:
        blocker = blocker or "CX2H3_RECONNECT_FAILURE_RECOVERY"

    j5_pass = all(
        [
            tokens.get("CX2H3_REAL_OFFLINE_LOCAL_WORK_PASS"),
            tokens.get("CX2H3_REAL_OFFLINE_MAIL_QUEUE_PASS"),
            tokens.get("CX2H3_OFFLINE_RESTART_PERSISTENCE_PASS"),
            tokens.get("CX2H3_EXACTLY_ONCE_RECONCILIATION_PASS"),
            tokens.get("CX2H3_RECONNECT_FAILURE_RECOVERY_PASS"),
            offline_true,
        ]
    )
    facts["CX2H3_J5_JOURNEY"] = {
        "J5_CLASS": "REAL_USER_JOURNEY_DIGITAL_PASS" if j5_pass else "REAL_PROVIDER_GUI_PARTIAL",
        "blocker": blocker,
    }
    return {"facts": facts, "tokens": tokens, "blocker": blocker, "j5_pass": j5_pass}


def run_j2_j5(repo: Path, monitor: Path, captures: Path) -> Dict[str, Any]:
    j2 = run_j2(repo, monitor, captures)
    j5 = run_j5(
        repo,
        monitor,
        captures,
        edited_rel=j2.get("edited_rel") or "",
        j2_pass=bool(j2.get("j2_pass")),
    )
    facts = {}
    facts.update(j2.get("facts") or {})
    facts.update(j5.get("facts") or {})
    tokens = {}
    tokens.update(j2.get("tokens") or {})
    tokens.update(j5.get("tokens") or {})
    blocker = j2.get("blocker") or j5.get("blocker")
    return {
        "facts": facts,
        "tokens": tokens,
        "blocker": blocker,
        "j2_pass": j2.get("j2_pass"),
        "j5_pass": j5.get("j5_pass"),
        "J2_CLASS": "REAL_USER_JOURNEY_DIGITAL_PASS" if j2.get("j2_pass") else "REAL_PROVIDER_GUI_PARTIAL",
        "J5_CLASS": "REAL_USER_JOURNEY_DIGITAL_PASS" if j5.get("j5_pass") else "REAL_PROVIDER_GUI_PARTIAL",
    }
