# Future — physical boot and factory

Not implemented in this checkout as proven evidence.

```mermaid
flowchart LR
  EVT[EVT assembly] --> FLASH[Signed factory flash]
  FLASH --> BOOT[Measured physical boot]
  BOOT --> OTA[Production OTA channel]
  OTA --> LAB[RF / thermal / battery lab]
```

Status words: `GUNNCHOS_PHYSICAL_BOOT_PENDING`,
`GUNNCHOS_PHYSICAL_SYSTEM_IMAGE_PENDING`, `PHYSICAL_EXECUTION_FREEZE`.

Do not treat `make bootable-reference` or Docker :8080 as this diagram.
