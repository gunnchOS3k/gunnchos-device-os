# Use case — current

Actors: student, guardian, educator, developer, research operator, CI/reproducer.
This repo does **not** execute RAN control or physical boot.

```mermaid
flowchart LR
  subgraph actors
    ST[Student]
    GU[Guardian]
    ED[Educator]
    DV[Developer]
    RO[Research operator]
    CI[CI / independent reproducer]
  end
  subgraph os [gunnchos-device-os digital path]
    UC1[Complete onboarding]
    UC2[Switch Campus / Game / Media / Offline mode]
    UC3[Launch first-party or policy-gated app]
    UC4[Evaluate service-continuity profile]
    UC5[Run software boot probe]
    UC6[Simulate OTA / rollback]
    UC7[Reproduce pytest + checksums]
  end
  ST --> UC1
  ST --> UC2
  ST --> UC3
  GU --> UC2
  ED --> UC2
  DV --> UC3
  DV --> UC5
  RO --> UC4
  RO --> UC5
  CI --> UC7
  CI --> UC4
```

RQ1 mapping: four research classes (desk / mobile-docked / local-creation / wearable)
are aliases of `config/device_classes.yaml` IDs — see
`gunnchos_device_os/service_continuity/`.

Code: `gunnchos_device_os/onboarding_wizard.py`, `mode_manager.py`, `launcher.py`,
`boot/probe.py`, `ota_state_machine.py`, `apps/launcher_mock`.
