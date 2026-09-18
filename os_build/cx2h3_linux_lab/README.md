# CX2H.3 Linux Lab — Browser + Mail + Offline/Reconnect

Child overlay of CX2H.2. Evidence: `artifacts/complete_experience/cx2h3/`.

Lock: `/tmp/gunnchos-cx-qemu.lock` — never kill foreign QEMU.

Host providers (stoppable for genuine offline):
- HTTPS on `:18443` (`scripts/cx2h3_host_https.py`)
- SMTP `:1587` + IMAP `:1143` (`scripts/cx2h3_host_mail.py`)

Guest reaches host via QEMU SLIRP `10.0.2.2` / `cx2h3.test`.
