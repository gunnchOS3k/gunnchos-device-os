# CX2H.4 Linux Lab — P0 Digital Closure Audit

Child overlay of CX2H.3. Evidence: `artifacts/complete_experience/cx2h4/`.

Lock: `/tmp/gunnchos-cx-qemu.lock` — one CX guest; never kill foreign QEMU.

Host providers:
- CalDAV/CardDAV + browser GUI on `:18580` (`scripts/cx2h4_host_caldav.py`)

Guest provider:
- Calc/Impress GUI + Chromium collab helpers on `:8769` (`scripts/cx2h4_provider.py`)

`FULL_COMPLETE_EXPERIENCE_COMPLETE=false`
