# Update / recovery activity — current simulation

Source: `gunnchos_device_os/ota_state_machine.py` `ALLOWED_TRANSITIONS`.
Not a live OTA channel. Make: no production signing.

```mermaid
flowchart TD
  IDLE[idle] --> CHECK[checking]
  CHECK -->|update found| DLWAIT[download_pending]
  CHECK -->|none| IDLE
  DLWAIT --> DL[downloading]
  DL --> VER[verifying]
  VER -->|digest+sig ok| STAGE[staging]
  VER -->|bad sig/corrupt| FAIL[failed]
  STAGE --> APPLY[applying]
  APPLY --> REBOOT[reboot_pending]
  REBOOT --> HEALTH[health_check]
  HEALTH -->|ok| COMMIT[committed]
  HEALTH -->|fail| RB[rolling_back]
  COMMIT --> IDLE
  RB --> ROLLED[rolled_back]
  ROLLED --> IDLE
  FAIL --> RB
  FAIL --> IDLE
```

Boot recovery playbook: `gunnchos_device_os/boot/recovery.py` `RECOVERY_PLAYBOOK`
(missing service, corrupt manifest, stale image, unsupported arch, storage, network).
