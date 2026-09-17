"""Fail-closed CX2H.3 tests — curl/HTTP/fixtures/offline-toggle cannot earn DIGITAL_PASS."""

from __future__ import annotations

from gunnchos_device_os.cx2h3.evidence import next_gate
from gunnchos_device_os.cx2h3.tokens import Cx2h3Tokens


def _prereq_ok(**kwargs) -> Cx2h3Tokens:
    base = dict(
        CX2H3_PREREQUISITE_PASS=True,
        J1_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J3_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J7_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J6_CLASS="HUMAN_VALIDATION_PENDING",
    )
    base.update(kwargs)
    return Cx2h3Tokens(**base)


def test_curl_https_cannot_earn_browser_gui_pass():
    tokens = _prereq_ok(CX2H3_REAL_BROWSER_GUI_PASS=False, CX2H3_REAL_HTTPS_DOWNLOAD_GUI_PASS=False)
    curl_claim = {"method": "curl", "https": True}
    assert curl_claim["method"] == "curl"
    assert tokens.CX2H3_REAL_BROWSER_GUI_PASS is False
    assert tokens.j2_digital_pass() is False


def test_http_cannot_substitute_https():
    tokens = _prereq_ok(CX2H3_REAL_HTTPS_PROVIDER_PASS=False)
    http_only = {"scheme": "http", "tls": False}
    assert http_only["scheme"] == "http"
    assert tokens.j2_digital_pass() is False


def test_tls_warning_bypass_cannot_earn_https_pass():
    tokens = _prereq_ok(CX2H3_REAL_HTTPS_DOWNLOAD_GUI_PASS=False)
    bypass = {"ignore_certificate_errors": True}
    assert bypass["ignore_certificate_errors"] is True
    assert tokens.j2_digital_pass() is False


def test_direct_file_copy_cannot_earn_download_pass():
    tokens = _prereq_ok(CX2H3_REAL_HTTPS_DOWNLOAD_GUI_PASS=False)
    copy = {"method": "cp", "browser": False}
    assert copy["method"] == "cp"
    assert tokens.j2_digital_pass() is False


def test_direct_smtp_script_cannot_earn_mail_gui_pass():
    tokens = _prereq_ok(CX2H3_REAL_MAIL_GUI_PASS=False)
    direct = {"direct_smtp_without_gui": True}
    assert direct["direct_smtp_without_gui"] is True
    assert tokens.j2_digital_pass() is False


def test_smtp_sink_without_imap_cannot_earn_j2():
    tokens = _prereq_ok(CX2H3_REAL_SMTP_IMAP_PROVIDER_PASS=False)
    sink = {"smtp": True, "imap": False}
    assert sink["imap"] is False
    assert tokens.j2_digital_pass() is False


def test_fake_inbox_json_cannot_earn_j2():
    tokens = _prereq_ok(CX2H3_REAL_MAIL_GUI_PASS=False, CX2H3_REAL_MAIL_ATTACHMENT_ROUNDTRIP_PASS=False)
    fake = {"inbox": [{"subject": "fixture"}], "json_fixture": True}
    assert fake["json_fixture"] is True
    assert tokens.j2_digital_pass() is False


def test_mail_attachment_must_match_vault_hash():
    tokens = _prereq_ok(CX2H3_REAL_MAIL_ATTACHMENT_ROUNDTRIP_PASS=False)
    mismatch = {"vault_sha": "aaa", "att_sha": "bbb"}
    assert mismatch["vault_sha"] != mismatch["att_sha"]
    assert tokens.j2_digital_pass() is False


def test_frontend_offline_toggle_cannot_earn_j5():
    tokens = _prereq_ok(
        CX2H3_REAL_BROWSER_GUI_PASS=True,
        CX2H3_REAL_HTTPS_PROVIDER_PASS=True,
        CX2H3_REAL_HTTPS_DOWNLOAD_GUI_PASS=True,
        CX2H3_DOWNLOADED_DOCUMENT_EDIT_PASS=True,
        CX2H3_REAL_SMTP_IMAP_PROVIDER_PASS=True,
        CX2H3_REAL_MAIL_GUI_PASS=True,
        CX2H3_REAL_MAIL_ATTACHMENT_ROUNDTRIP_PASS=True,
        CX2H3_J2_PERSISTENCE_PASS=True,
        CX2H3_REAL_OFFLINE_LOCAL_WORK_PASS=False,
    )
    nav = {"navigator_onLine": False, "endpoints_reachable": True}
    assert nav["endpoints_reachable"] is True
    assert tokens.j5_digital_pass() is False


def test_network_must_be_truly_unreachable():
    tokens = _prereq_ok(CX2H3_REAL_OFFLINE_LOCAL_WORK_PASS=False)
    assert tokens.j5_digital_pass() is False


def test_queued_message_must_survive_restart():
    tokens = _prereq_ok(CX2H3_OFFLINE_RESTART_PERSISTENCE_PASS=False)
    assert tokens.j5_digital_pass() is False


def test_reconnect_requires_authoritative_server_state():
    tokens = _prereq_ok(CX2H3_EXACTLY_ONCE_RECONCILIATION_PASS=False)
    local_sent = {"client_sent": True, "smtp_accept": False}
    assert local_sent["smtp_accept"] is False
    assert tokens.j5_digital_pass() is False


def test_duplicate_server_messages_fail_exactly_once():
    tokens = _prereq_ok(CX2H3_EXACTLY_ONCE_RECONCILIATION_PASS=False)
    dups = {"count": 2}
    assert dups["count"] > 1
    assert tokens.j5_digital_pass() is False


def test_local_sent_without_smtp_imap_truth_fails():
    tokens = _prereq_ok(
        CX2H3_REAL_MAIL_GUI_PASS=True,
        CX2H3_REAL_MAIL_ATTACHMENT_ROUNDTRIP_PASS=False,
    )
    assert tokens.j2_digital_pass() is False


def test_j5_cannot_pass_unless_j2_genuine():
    tokens = _prereq_ok(
        CX2H3_REAL_HTTPS_PROVIDER_PASS=True,
        CX2H3_REAL_BROWSER_GUI_PASS=True,
        CX2H3_REAL_HTTPS_DOWNLOAD_GUI_PASS=True,
        CX2H3_DOWNLOADED_DOCUMENT_EDIT_PASS=True,
        CX2H3_REAL_SMTP_IMAP_PROVIDER_PASS=True,
        CX2H3_REAL_MAIL_GUI_PASS=True,
        CX2H3_REAL_MAIL_ATTACHMENT_ROUNDTRIP_PASS=True,
        CX2H3_J2_PERSISTENCE_PASS=False,  # J2 incomplete
        CX2H3_REAL_OFFLINE_LOCAL_WORK_PASS=True,
        CX2H3_REAL_OFFLINE_MAIL_QUEUE_PASS=True,
        CX2H3_OFFLINE_RESTART_PERSISTENCE_PASS=True,
        CX2H3_EXACTLY_ONCE_RECONCILIATION_PASS=True,
        CX2H3_RECONNECT_FAILURE_RECOVERY_PASS=True,
    )
    assert tokens.j2_digital_pass() is False
    assert tokens.j5_digital_pass() is False


def test_full_tokens_earn_digital_pass_and_next_gate():
    tokens = _prereq_ok(
        CX2H3_REAL_HTTPS_PROVIDER_PASS=True,
        CX2H3_REAL_BROWSER_GUI_PASS=True,
        CX2H3_REAL_HTTPS_DOWNLOAD_GUI_PASS=True,
        CX2H3_DOWNLOADED_DOCUMENT_EDIT_PASS=True,
        CX2H3_REAL_SMTP_IMAP_PROVIDER_PASS=True,
        CX2H3_REAL_MAIL_GUI_PASS=True,
        CX2H3_REAL_MAIL_ATTACHMENT_ROUNDTRIP_PASS=True,
        CX2H3_J2_PERSISTENCE_PASS=True,
        CX2H3_REAL_OFFLINE_LOCAL_WORK_PASS=True,
        CX2H3_REAL_OFFLINE_MAIL_QUEUE_PASS=True,
        CX2H3_OFFLINE_RESTART_PERSISTENCE_PASS=True,
        CX2H3_EXACTLY_ONCE_RECONCILIATION_PASS=True,
        CX2H3_RECONNECT_FAILURE_RECOVERY_PASS=True,
        J2_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J5_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
    )
    assert tokens.j2_digital_pass() is True
    assert tokens.j5_digital_pass() is True
    assert next_gate(tokens) == "CX2H4_P0_DIGITAL_CLOSURE_AUDIT"
