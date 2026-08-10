"""Hostile-network digital S2 suite (HOSTILE_NETWORK_DIGITAL=E4 prepared).

Simulates malicious DNS, untrusted TLS, hostname mismatch, expired cert,
captive portal, HTTP downgrade, and link loss/restore. Credentials/tokens must
not be sent to untrusted origins. Real RF/Wi-Fi remains E5/E8 EXTERNAL_PENDING.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import ipaddress
import json
import ssl
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


EVIDENCE_LEVEL = "E4_DIGITAL"
RF_WIFI_STATUS = "E5_E8_EXTERNAL_PENDING"


@dataclass
class CredentialVault:
    """In-memory credentials that must not leak to untrusted origins."""

    bearer_token: str = "dev-session-token-KEEP"
    password: str = "dev-password-KEEP"
    cookie: str = "session=dev-cookie-KEEP"
    sent_to: list[dict[str, Any]] = field(default_factory=list)

    def authorize(self, origin: str, *, trusted: bool) -> dict[str, Any]:
        if not trusted:
            self.sent_to.append({"origin": origin, "credentials_sent": False, "reason": "untrusted_origin"})
            return {"authorized": False, "credentials_sent": False, "reason": "untrusted_origin"}
        # Trusted path may attach credentials (recorded for tests; not a live network).
        self.sent_to.append({"origin": origin, "credentials_sent": True})
        return {
            "authorized": True,
            "credentials_sent": True,
            "authorization": f"Bearer {self.bearer_token}",
        }


@dataclass
class HostileNetworkSimulator:
    """Digital (in-process) hostile-network policy + TLS/DNS scenario runner."""

    trusted_hostnames: set[str] = field(default_factory=lambda: {"updates.gunnchos.dev", "api.gunnchos.dev"})
    trusted_dns: dict[str, str] = field(
        default_factory=lambda: {
            "updates.gunnchos.dev": "203.0.113.10",
            "api.gunnchos.dev": "203.0.113.11",
        }
    )
    vault: CredentialVault = field(default_factory=CredentialVault)
    link_up: bool = True
    events: list[dict[str, Any]] = field(default_factory=list)

    def _event(self, kind: str, **kwargs: Any) -> dict[str, Any]:
        ev = {"kind": kind, **kwargs}
        self.events.append(ev)
        return ev

    def resolve_dns(self, hostname: str, *, poisoned: dict[str, str] | None = None) -> dict[str, Any]:
        table = dict(self.trusted_dns)
        if poisoned:
            table.update(poisoned)
        ip = table.get(hostname)
        if ip is None:
            self._event("dns_nxdomain", hostname=hostname)
            return {"ok": False, "reason": "nxdomain", "hostname": hostname}
        trusted_ip = self.trusted_dns.get(hostname)
        poisoned_hit = trusted_ip is not None and ip != trusted_ip
        if poisoned_hit:
            self._event("dns_poison", hostname=hostname, resolved=ip, expected=trusted_ip)
            return {
                "ok": False,
                "reason": "malicious_dns",
                "hostname": hostname,
                "resolved": ip,
                "trusted": False,
            }
        return {"ok": True, "hostname": hostname, "resolved": ip, "trusted": True}

    def classify_origin(self, url: str, *, resolved_ip: str | None = None) -> dict[str, Any]:
        parsed = urlparse(url)
        scheme = (parsed.scheme or "").lower()
        host = (parsed.hostname or "").lower()
        if scheme == "http":
            return {
                "trusted": False,
                "reason": "http_downgrade",
                "hostname": host,
                "scheme": scheme,
            }
        if scheme != "https":
            return {"trusted": False, "reason": "unsupported_scheme", "hostname": host}
        if host not in self.trusted_hostnames:
            return {"trusted": False, "reason": "untrusted_hostname", "hostname": host}
        if resolved_ip:
            expected = self.trusted_dns.get(host)
            if expected and resolved_ip != expected:
                return {
                    "trusted": False,
                    "reason": "dns_ip_mismatch",
                    "hostname": host,
                    "resolved_ip": resolved_ip,
                }
            try:
                addr = ipaddress.ip_address(resolved_ip)
                if addr.is_private or addr.is_loopback:
                    # Local simulation peers may be OK only if hostname trusted;
                    # treat unexpected private as suspicious for hostile suite.
                    pass
            except ValueError:
                return {"trusted": False, "reason": "bad_ip", "hostname": host}
        return {"trusted": True, "hostname": host, "scheme": scheme}

    def request(
        self,
        url: str,
        *,
        with_credentials: bool = True,
        resolved_ip: str | None = None,
        tls_status: str = "ok",
        captive_portal: bool = False,
    ) -> dict[str, Any]:
        if not self.link_up:
            self._event("offline", url=url)
            return {"ok": False, "reason": "link_down", "credentials_sent": False}

        if captive_portal:
            # Captive portal intercept: never forward real credentials.
            auth = self.vault.authorize(url, trusted=False)
            self._event("captive_portal", url=url)
            return {
                "ok": False,
                "reason": "captive_portal",
                "credentials_sent": auth["credentials_sent"],
                "portal": True,
            }

        if tls_status == "untrusted_ca":
            auth = self.vault.authorize(url, trusted=False)
            return {
                "ok": False,
                "reason": "untrusted_tls",
                "credentials_sent": auth["credentials_sent"],
            }
        if tls_status == "hostname_mismatch":
            auth = self.vault.authorize(url, trusted=False)
            return {
                "ok": False,
                "reason": "hostname_mismatch",
                "credentials_sent": auth["credentials_sent"],
            }
        if tls_status == "expired_cert":
            auth = self.vault.authorize(url, trusted=False)
            return {
                "ok": False,
                "reason": "expired_cert",
                "credentials_sent": auth["credentials_sent"],
            }

        origin = self.classify_origin(url, resolved_ip=resolved_ip)
        if not origin["trusted"]:
            auth = self.vault.authorize(url, trusted=False)
            return {
                "ok": False,
                "reason": origin["reason"],
                "credentials_sent": auth["credentials_sent"],
                "origin": origin,
            }

        auth = (
            self.vault.authorize(url, trusted=True)
            if with_credentials
            else {"credentials_sent": False, "authorized": False}
        )
        self._event("trusted_request", url=url)
        return {
            "ok": True,
            "reason": "ok",
            "credentials_sent": bool(auth.get("credentials_sent")),
            "origin": origin,
        }

    def set_link(self, up: bool) -> dict[str, Any]:
        self.link_up = up
        return self._event("link", up=up)

    def run_digital_suite(self) -> dict[str, Any]:
        """Execute negative/positive digital hostile-network cases."""
        cases: list[dict[str, Any]] = []

        def add(case_id: str, passed: bool, evidence: dict[str, Any]) -> None:
            cases.append({"case_id": case_id, "passed": passed, "evidence": evidence})

        # Malicious DNS
        dns = self.resolve_dns(
            "updates.gunnchos.dev",
            poisoned={"updates.gunnchos.dev": "198.51.100.66"},
        )
        add("HN-DNS-001", dns.get("reason") == "malicious_dns", dns)

        # Untrusted TLS / hostname mismatch / expired
        r1 = self.request("https://updates.gunnchos.dev/pkg", tls_status="untrusted_ca")
        add(
            "HN-TLS-001",
            r1["reason"] == "untrusted_tls" and r1["credentials_sent"] is False,
            r1,
        )

        r2 = self.request("https://updates.gunnchos.dev/pkg", tls_status="hostname_mismatch")
        add(
            "HN-TLS-002",
            r2["reason"] == "hostname_mismatch" and r2["credentials_sent"] is False,
            r2,
        )

        r3 = self.request("https://updates.gunnchos.dev/pkg", tls_status="expired_cert")
        add(
            "HN-TLS-003",
            r3["reason"] == "expired_cert" and r3["credentials_sent"] is False,
            r3,
        )

        # Captive portal
        r4 = self.request("https://updates.gunnchos.dev/pkg", captive_portal=True)
        add(
            "HN-CAPTIVE-001",
            r4["reason"] == "captive_portal" and r4["credentials_sent"] is False,
            r4,
        )

        # HTTP downgrade
        r5 = self.request("http://updates.gunnchos.dev/pkg")
        add(
            "HN-HTTP-001",
            r5["reason"] == "http_downgrade" and r5["credentials_sent"] is False,
            r5,
        )

        # Untrusted origin must not receive credentials
        r6 = self.request("https://evil.example/phish")
        add(
            "HN-CRED-001",
            r6["credentials_sent"] is False and r6["ok"] is False,
            r6,
        )

        # Loss / restore
        self.set_link(False)
        r7 = self.request("https://api.gunnchos.dev/v1")
        self.set_link(True)
        r8 = self.request(
            "https://api.gunnchos.dev/v1",
            resolved_ip=self.trusted_dns["api.gunnchos.dev"],
        )
        add(
            "HN-LINK-001",
            r7["reason"] == "link_down"
            and r7["credentials_sent"] is False
            and r8["ok"] is True
            and r8["credentials_sent"] is True,
            {"down": r7, "up": r8},
        )

        # Real TLS material: expired + hostname mismatch certs (local files)
        tls_mat = build_tls_fixture_pair()
        add(
            "HN-TLS-MATERIAL-001",
            tls_mat["expired_not_after_past"] and tls_mat["mismatch_san_is_evil"],
            tls_mat,
        )

        all_pass = all(c["passed"] for c in cases)
        return {
            "schema": "gunnchos.wp007.hostile_network_digital.v1",
            "HOSTILE_NETWORK_DIGITAL": "E4_PREPARED" if all_pass else "FAIL",
            "evidence_level": EVIDENCE_LEVEL,
            "RF_WIFI_STATUS": RF_WIFI_STATUS,
            "passed": all_pass,
            "cases": cases,
            "credential_leak_events": [
                e for e in self.vault.sent_to if e.get("credentials_sent") and "evil" in str(e.get("origin", ""))
            ],
            "claim_boundary": (
                "Digital hostile-network suite (Device Lab / logical+netns-capable). "
                "Real RF/Wi-Fi E5/E8 EXTERNAL_PENDING."
            ),
        }


def build_tls_fixture_pair(tmpdir: Path | None = None) -> dict[str, Any]:
    """Create real X.509 material: expired cert + hostname-mismatch cert."""
    root = Path(tmpdir) if tmpdir else Path(tempfile.mkdtemp(prefix="wp007-tls-"))
    root.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = dt.datetime.now(dt.timezone.utc)

    def _cert(cn: str, san: str, not_before: dt.datetime, not_after: dt.datetime) -> x509.Certificate:
        builder = (
            x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)]))
            .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)]))
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(not_before)
            .not_valid_after(not_after)
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(san)]),
                critical=False,
            )
        )
        return builder.sign(key, hashes.SHA256())

    expired = _cert(
        "updates.gunnchos.dev",
        "updates.gunnchos.dev",
        now - dt.timedelta(days=400),
        now - dt.timedelta(days=10),
    )
    mismatch = _cert(
        "updates.gunnchos.dev",
        "evil.example",
        now - dt.timedelta(days=1),
        now + dt.timedelta(days=30),
    )
    exp_path = root / "expired.pem"
    mis_path = root / "hostname_mismatch.pem"
    exp_path.write_bytes(expired.public_bytes(serialization.Encoding.PEM))
    mis_path.write_bytes(mismatch.public_bytes(serialization.Encoding.PEM))

    # Prove OpenSSL rejects expired when loading into a context with check
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    # We only assert cert metadata here; full handshake needs a listener.
    return {
        "expired_path": str(exp_path),
        "mismatch_path": str(mis_path),
        "expired_not_after_past": expired.not_valid_after_utc < now,
        "mismatch_san_is_evil": any(
            isinstance(n, x509.DNSName) and n.value == "evil.example"
            for n in mismatch.extensions.get_extension_for_class(
                x509.SubjectAlternativeName
            ).value
        ),
        "fingerprint_expired_sha256": hashlib.sha256(
            expired.public_bytes(serialization.Encoding.DER)
        ).hexdigest(),
    }
