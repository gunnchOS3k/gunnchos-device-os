# gunnchOS Device Capability Adapters

**Status:** VXP-2 universal parity addendum  
**Governs under:** `docs/product/GUNNCHOS_DEVICE_PARITY_CONTRACT.md`  
**Code anchors:** `apps/gunnch_shell/src/platform/capsuleBridge.ts`, `apps/gunnchos_capsule_android/.../CapabilityRouter.kt`

---

## Purpose

Adapters translate **one gunnchOS** onto host hardware. They enhance presentation and input. They must **not** create separate OS identities (no “phone OS” vs “laptop OS” products).

Rule reminder:

| Capability state | Adapter behavior |
|------------------|------------------|
| Present | Enhanced native path |
| Absent | Fallback path, same surface |
| Impossible | Preserve place + honest limitation |

---

## Adapter catalog (examples)

### Camera
- **Present:** Creation / Care / verification flows request `camera` via bridge; host opens permission-mediated capture.
- **Absent:** File/document pick fallback (`file_picker` / Vault).
- **Evidence today:** `CapabilityRouter.gatedMedia("camera")` — permission stub, `capture_started: false` → enhancement **not** fully wired (`NOT_IMPLEMENTED` for capture UX).

### Microphone
- Same pattern as camera (`RECORD_AUDIO`).
- Fallback: text input for gunnchAI / Connect compose.
- Evidence: stub ready, no capture pipeline.

### Pen / stylus
- **Present (tablet / DS-XL):** Creation canvas inking; note markup in Vault.
- **Absent (Pixel phone):** finger draw or import image; preserve Creation place.
- Evidence: no pen capability in Capsule bridge → `NOT_IMPLEMENTED` adapter.

### Gamepad
- **Present (handheld):** Gaming library focuses titles; in-game HID.
- **Absent:** on-screen controls / touch.
- Evidence: no `gamepad` capability in bridge; Games matrix is launch-metadata only.

### External display / docking
- **Present:** extend Living Workspace rail layout; Continuity session on external.
- **Absent:** single display immersive (Capsule default).
- Evidence: `display` capability toggles immersive + metrics only; no multi-display → `NOT_IMPLEMENTED` for extend.

### Local AI runtime
- **Present:** gunnchAI on-device / guest weights.
- **Absent:** offline canned help + honest “model unavailable.”
- Evidence: `GunnchAiProvider.launch` returns flags (`offlineFallback`, `textHelp`) without UI route → full route `NOT_IMPLEMENTED`.

### Nearby edge runtime
- **Present:** edge-io / remote-edge catalog entries enhance measurement Continuity.
- **Absent:** local-only status.
- Evidence: App Center lists `remote-edge` as optional/not installed; Edge IO wearables are sibling-repo / device-class docs, not Capsule shell routes.

### Wearable sensors / wearable inputs
- **Present:** Care / Continuity / research glance modules.
- **Impossible on phone alone:** preserve wearable domain via paired Continuity; do not delete Care.
- Evidence: bluetooth/usb metadata-only in router; no wearable input adapter.

### Haptics
- **Present:** confirmations, game events, Assist feedback (`haptics` one-shot vibrate).
- **Absent:** visual/audio only.
- Evidence: Capsule implements basic vibrate — **enhanced native** for phone class.

### Telephony
- **Present:** Connect can offer dial/SMS intents where platform allows.
- **Absent / restricted:** mail/calendar-only Connect; honest limitation.
- Evidence: Connect is local compose UI; no telephony capability → fallback Communication without cellular.

### GNSS / motion sensors
- **Present:** leisure/maps, game context, edge measurement.
- **Absent:** manual location / skip.
- Evidence: not exposed on Capsule bridge → `NOT_IMPLEMENTED`.

### Keyboard / mouse / windowing
- **Present (14.5" / DS-XL):** Alt+1..0 shortcuts, rail layout (`matchMedia` wide), multi-window future.
- **Absent (phone):** dock + soft keyboard.
- Evidence: shell already adapts dock vs rail — **presentation adapter** working; freeform windowing `NOT_IMPLEMENTED`.

### Background execution
- **Present:** `CapsuleForegroundService` keeps Capsule session policy honest on Android.
- **Restricted hosts:** degrade Continuity messaging.
- Evidence: foreground service exists — Android adapter present.

### Platform permissions
- Central consent via `permissions` capability + Assist settings readouts.
- Never silent install (`AppCenterProvider.silentInstallForbidden`).

---

## Shared components vs host adapters

```
Shared surface (React) ──invoke──► Bridge allowlist ──► Host provider / OS API
        │                                    │
        └── EmptyState / honest limit ◄──────┘ when absent/impossible
```

- Shared: Home, Vault, App Center, Connect, Assist, Care, Wallet, …  
- Host: Kotlin providers, Linux guest, PWA Custom Tabs, future native SKUs.

---

## Anti-patterns (forbidden)

1. Shipping Capsule as “companion to real gunnchOS.”  
2. Removing WAIKE/Games/Creation from phone because adapters are incomplete.  
3. Forking separate design systems per form factor without shared tokens.  
4. Copying Apple control layouts/gestures/terminology as the adapter UX.

---

## Next implementation actions (adapter-shaped)

See gap map: `docs/product/GUNNCHOS_ANDROID_FULL_EXPERIENCE_GAPS.md`.
