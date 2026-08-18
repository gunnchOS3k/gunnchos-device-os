# Package / repository relationship — current

This repo is RQ1 core infrastructure. It does not vendor RAN or hardware CAD.

```mermaid
flowchart TB
  OS[gunnchos-device-os]
  subgraph local [this checkout]
    GOPY[gunnchos_device_os]
    LM[apps/launcher_mock]
    CFG[config]
    OSB[os_build]
    TST[tests]
  end
  subgraph siblings [sibling repos - contracts only]
    HW[hardware-industrial-design]
    AI[gunnchAI3k]
    WK[waike-research-ops]
    EIO[edge-io-measurement-node]
    T7[7gc-digital-twin]
  end
  OS --> GOPY
  OS --> LM
  OS --> CFG
  OS --> OSB
  OS --> TST
  GOPY -.-> HW
  GOPY -.-> AI
  GOPY -.-> WK
  GOPY -.-> EIO
  GOPY -.-> T7
```

Firmware/hardware manifests are **mirrored and simulated** here
(`hardware_compat/`, `cross_repo_firmware_bridge/`). Physical board proof remains pending.
