# Capsule Architecture

**Product identity:** Android Capsule is an **Android-hosted expression of the same gunnchOS**, not a companion app, reduced mobile shell, or launcher-only wrapper. Governing contract: [`docs/product/GUNNCHOS_DEVICE_PARITY_CONTRACT.md`](../product/GUNNCHOS_DEVICE_PARITY_CONTRACT.md).

```
Android Host (stock Pixel)
  └─ CapsuleActivity + ForegroundService
       └─ WebView embeds production apps/gunnch_shell assets
            └─ hostRuntime: ANDROID_CAPSULE | GUNNCHOS_LINUX | WEB_TEST
                 └─ CapsuleBridge (allowlisted JS↔Kotlin)
                      ├─ Android Bridge providers (files/share/camera/…)
                      ├─ Local providers (Vault/AppCenter/Games/…)
                      ├─ Optional Linux Guest (NONE|QEMU_TCG|AVF_EXPERIMENTAL|REMOTE_EDGE)
                      └─ Edge / PWA (WAIKE) — adapters, not a separate OS
```

Truth boundary: `GUNNCHOS_CAPSULE_EXPERIENCE_PARITY` — not kernel identity. Universal parity gates: `artifacts/vxp2/reports/GUNNCHOS_UNIVERSAL_PARITY_GATES.json` (human gates remain false until owner review).
