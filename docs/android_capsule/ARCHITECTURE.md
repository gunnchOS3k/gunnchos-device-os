# Capsule Architecture

```
Android Host (stock Pixel)
  └─ CapsuleActivity + ForegroundService
       └─ WebView embeds production apps/gunnch_shell assets
            └─ hostRuntime: ANDROID_CAPSULE | GUNNCHOS_LINUX | WEB_TEST
                 └─ CapsuleBridge (allowlisted JS↔Kotlin)
                      ├─ Android Bridge providers (files/share/camera/…)
                      ├─ Local providers (Vault/AppCenter/Games/…)
                      ├─ Optional Linux Guest (NONE|QEMU_TCG|AVF_EXPERIMENTAL|REMOTE_EDGE)
                      └─ Edge / PWA (WAIKE)
```

Truth boundary: `GUNNCHOS_CAPSULE_EXPERIENCE_PARITY` — not kernel identity.
