# Phase XIII Stage 2 — OS foundations

Lanes: **OS-BASE** (image/A-B/recovery), **gunnchShell** (Weston + adaptive profiles),
**compat** (runtime lanes + corpus), **security** (trust/sandbox/modes).

- Build: `make -C os_build/stage2 image`
- Prove: `python3 scripts/prove_stage2_os.py` → `artifacts/stage2/OS_PROVE_REPORT.json`
- CI: `.github/workflows/stage2-frontier-os.yml`

`PHYSICAL_EXECUTION_FREEZE=ACTIVE`. Does **not** claim `GUNNCHOS_FRONTIER_OS_PARITY`.
