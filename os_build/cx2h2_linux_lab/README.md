# CX2H.2 Linux lab — document/print/recovery J1+J7 on CX2H stack

Isolated from Device Lab. Child qcow2 overlay backs onto immutable CX2H overlay.

```bash
python -m gunnchos_device_os.cx2h2 --prepare-only
python -m gunnchos_device_os.cx2h2 --cx2h2
```

Evidence: `artifacts/complete_experience/cx2h2/`
Lock: `/tmp/gunnchos-cx-qemu.lock`
Runtime: `/tmp/cx2h2-graphical/`

Never kill foreign QEMU. `PHYSICAL_PRINTER_PENDING=true` always.
