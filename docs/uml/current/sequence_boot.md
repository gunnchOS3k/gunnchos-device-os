# Boot sequence — current software probe

Source: `gunnchos_device_os/boot/probe.py` `run_boot_probe`, Make `gate1-boot`.

Always co-emits `GUNNCHOS_PHYSICAL_BOOT_PENDING`. Physical capture is a separate path
(`gunnchos_device_os/boot/physical.py`) and is not claimed here.

```mermaid
sequenceDiagram
  participant Make as make gate1-boot
  participant CLI as python -m gunnchos_device_os.boot
  participant Man as load_boot_manifest
  participant Probe as run_boot_probe
  participant Rec as boot/recovery.py
  participant Out as results/gate1/boot_evidence.json
  Make->>CLI: --manifest config/boot/sample_manifest.json
  CLI->>Man: validate JSON
  alt corrupted / injected failure
    Man-->>CLI: BootManifestError
    CLI->>Rec: recovery_for_errors
    CLI->>Out: SOFTWARE_PATH_FAIL + PHYSICAL_BOOT_PENDING
  else valid manifest
    CLI->>Probe: arch, storage, display env, network, services
    Probe-->>CLI: BootProbeResult
    CLI->>Out: SOFTWARE_PASS + PHYSICAL_BOOT_PENDING
  end
```

Make target: `gate1-boot` / `gate1-test`.
