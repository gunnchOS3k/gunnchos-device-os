# CX2H Linux lab — portal session + J3 App Center on CX2G stack

Isolated from Device Lab. Clones CX2G overlay as backing file (CX2G immutable).

```bash
python -m gunnchos_device_os.cx2h --prepare-only
python -m gunnchos_device_os.cx2h --cx2h1
```

Evidence: `artifacts/complete_experience/cx2h/`

Lock: `/tmp/gunnchos-cx-qemu.lock` — never kill foreign QEMU.
