# gunnchOS Universal Device Parity Contract

**Program:** Capsule VXP-2 addendum  
**Status:** governing product contract (superseding)  
**Evidence home:** `gunnchos-device-os`  
**Truth artifacts:** `artifacts/vxp2/reports/GUNNCHOS_FORM_FACTOR_PARITY_MATRIX.json`, `docs/product/GUNNCHOS_ANDROID_FULL_EXPERIENCE_GAPS.md`

---

## 0. Governing override (VXP-2)

This addendum supersedes prior interpretations of VXP-2 as Android-reduced, companion-only, launcher-only, or form-factor-specific.

This document **supersedes** any prior interpretation of Capsule VXP-2 (or Android Capsule) as:

- Android-only / phone-only identity  
- reduced mobile shell  
- companion app to a “real” OS elsewhere  
- launcher-only directory of apps  

**Principle:** One gunnchOS across devices. Adapt presentation and interaction only where hardware or platform requires it. **Android Capsule is an Android-hosted expression of the same OS**, not a companion.

Cross-platform conceptual models (shared identity + form-factor adaptation) may inform architecture. Do **not** copy Apple trade dress, layouts, icons, gestures, terminology, or animations.

Prior VXP docs that framed Capsule as companion or Android-reduced must defer here. See `docs/vxp/README.md` and `docs/android_capsule/ARCHITECTURE.md`.

---

## 1. One product family

Shared product surfaces (same family, adapted chrome):

| Surface | Role |
|---------|------|
| **Home** | System surface — continue / context modules (not an app directory) |
| **App Library / App Center** | Enumeration, install/open, provenance |
| **WAIKE** | Learning OS entry and continuity |
| **gunnchAI** | Assistant / local help |
| **Gaming** | Game library + launch matrix |
| **Creation** | Creator workflows |
| **Communication** | Connect (mail/calendar/contacts local) |
| **Leisure** | Media / rest / non-game leisure |
| **Vault** | Files kept and recovered |
| **Connect** | Messaging / calendar intents |
| **Assist** | Accessibility mechanics |
| **Care** | Backup / recovery |
| **Wallet / Portfolio / Career / Verifier** | Credential and evidence spine |
| **Search / Command** | System find + command |
| **Settings** | System preferences |
| **Continuity** | Session restore / handoff / resume |

---

## 2. Capability model

Every form factor publishes a capability profile. Dimensions (minimum set):

| Dimension | Meaning (examples) |
|-----------|--------------------|
| `display_class` | phone / handheld / tablet / laptop / desktop / wearable / external |
| `orientation` | portrait-primary / landscape-primary / rotate / fixed |
| `touch` | none / single / multi |
| `mouse` | none / pointer |
| `keyboard` | none / soft / hardware |
| `gamepad` | none / hid / platform |
| `pen` | none / stylus |
| `camera` | none / front / rear / multi |
| `microphone` | none / present |
| `speakers` | none / mono / stereo |
| `haptics` | none / basic / rich |
| `telephony` | none / cellular |
| `GNSS` | none / present |
| `motion_sensors` | none / imu |
| `wearable_inputs` | none / band / ring / arena |
| `external_display` | none / mirror / extend |
| `docking` | none / usb-c / proprietary dock |
| `local_compute_class` | low / mid / high |
| `GPU_class` | none / integrated / discrete |
| `local_AI_runtime` | none / on-device / guest |
| `nearby_edge_runtime` | none / lan / edge-io |
| `network_type` | offline / wifi / cellular / dual |
| `storage_class` | constrained / standard / expandable |
| `battery_class` | tethered / phone / handheld / laptop |
| `windowing_support` | single / multi / freeform |
| `background_execution` | restricted / service / daemon |
| `platform_permissions` | host-mediated consent model |

### Capability rules

1. **Present → enhanced native** — use the capability in-place (camera capture, pen inking, gamepad focus, external display layout).  
2. **Absent → fallback** — same surface, degraded path (file pick instead of camera; touch instead of pen; on-screen controls instead of gamepad).  
3. **Impossible → preserve place + honest limitation** — keep the surface/route; show an honest empty/limit state; never silently remove the product identity.

Adapters document: `docs/product/GUNNCHOS_DEVICE_CAPABILITY_ADAPTERS.md`.

---

## 3. Parity classification enum

| Class | Meaning |
|-------|---------|
| `FULL_NATIVE` | First-party native implementation on this host |
| `FULL_VIA_ADAPTER` | Same product surface via host bridge/adapters (e.g. Capsule WebView + providers) |
| `COMPANION` | **Disallowed as OS identity.** Allowed only as a *seed/handoff package* label for thin discovery trees — never as Capsule/product identity |
| `FALLBACK` | Surface exists; capability or depth intentionally degraded with honesty |
| `UNAVAILABLE_PLATFORM_LIMIT` | Host/platform cannot provide the capability; place preserved |
| `NOT_IMPLEMENTED` | Product gap — route/surface/wiring missing or stub-only |

Honest `NOT_IMPLEMENTED` beats greenwashing.

---

## 4. Form-factor intent

| Form factor | Intent |
|-------------|--------|
| **Phone / Android Capsule** | Full gunnchOS on stock Android host (Pixel reference). Immersive OS chrome; not a launcher widget. |
| **Handheld Hybrid** | Landscape-first gaming + study; dock/rail adapts; gamepad enhancement. |
| **Student 14.5"** | Laptop-like study/create; keyboard/mouse primary; rail navigation. |
| **DS-XL Coder** | Desktop/coder windowing; deep Settings; local compute/GPU class high. |
| **Edge IO / Wearables** | Measurement/context companions *to the OS family* — sensors enhance Continuity/Care/Research; they are not a reduced phone OS. |

Device profiles already referenced in shell: `student_14_5`, `handheld_hybrid`, `ds_xl`, `docked`, `ci_qemu` (`CompleteExperienceShell.tsx`).

---

## 5. Home as system surface

Home is **not** an app directory.

Required modules:

- **Continue / context** — resume last real sessions (SessionStore); empty state must stay honest (no invented recents).  
- **Spaces by purpose** — deep links into domains.  
- **System status** — connectivity, known blockers, a11y entry.  

**App Library / App Center** owns enumeration, install, open, provenance.

Evidence today: `HomeSurface.tsx` Continue is honest-empty; Spaces list Vault/App Center/Connect/Wallet/… — WAIKE/gunnchAI/Games/Creation not yet first-class Home modules (`NOT_IMPLEMENTED` as Home domains).

---

## 6. Shared navigation grammar

Same grammar on every form factor; **presentation adapts**:

| Grammar slot | Presentation examples |
|--------------|------------------------|
| Home | Dock / rail / wearable glance |
| Apps (App Library) | Dock / rail / library sheet |
| Search / Command | Palette / bar / voice stub |
| Continuity | Continue module / handoff chip |
| Notifications / Status | Banner / tray / wearable alert |
| Settings | Full surface (Assist is a11y subset, not Settings substitute) |

VXP-1 dock/rail (Home, Vault, App Center, Connect, More) is the **current** chrome. Universal grammar above is the **contract target**; missing slots are gaps, not permission to drop identity.

---

## 7. Domain requirements (contract)

### WAIKE
Full learning route on every form factor: open courses, continue lesson, offline honesty, handoff to Learning OS SoR when present. Capsule may use PWA/Custom Tab **as adapter**, not as “companion-only product.”

### gunnchAI
Full assistant route: ask, local/offline fallback, permission-gated tools, WAIKE handoff. Launch JSON without UI is `NOT_IMPLEMENTED` for full route.

### Gaming
Game **library** surface + launch matrix (native / capsule web / guest). Four-game matrix code ≠ library UX.

### Creation
Creator modes entry (artist/writer/music/…) from shell — not only `apps/creator_studio` seed HTML.

### Communication
Connect: compose, queue offline, calendar events — local protocols; no false Gmail/Outlook claims.

### Leisure
Dedicated leisure/media place (non-game). Currently absent → `NOT_IMPLEMENTED`.

### Search / Command
System-wide find + command. In-surface Vault/App search alone does not satisfy.

### Continuity
Session restore across Capsule relaunch; Home Continue populated from real sessions; cross-device handoff when capability present.

---

## 8. Shared design system + adapters pattern

| Layer | Location / rule |
|-------|-----------------|
| Tokens / icons / primitives | `apps/gunnch_shell/src/design/` |
| Living Workspace chrome | `CompleteExperienceShell.tsx` + `cx2.css` / `tokens.css` |
| Host runtime | `hostRuntime.ts` — `ANDROID_CAPSULE` \| `GUNNCHOS_LINUX` \| `WEB_TEST` |
| Capability bridge | `capsuleBridge.ts` ↔ Kotlin `CapabilityRouter` |
| Domain providers | `WaikeProvider`, `GunnchAiProvider`, `GamesProvider`, Vault, AppCenter, … |

**Pattern:** shared React surfaces + host adapters. Enhancements plug in via capabilities; they do not fork a separate OS identity per device.

---

## 9. Android Pixel end-to-end ecosystem journey (required)

On Pixel Capsule reference device, a single user must be able to journey:

1. Boot Capsule → Living Workspace Home (branded gunnchOS, not “companion”).  
2. Continue or open Spaces → App Library.  
3. Launch **WAIKE** full learning path (adapter OK).  
4. Launch **gunnchAI** full assistant path.  
5. Open **Games** library → launch at least one matrix title and return.  
6. Open **Creation** place (or honest limit).  
7. **Connect** send/queue; **Vault** file; **Care** snapshot.  
8. **Search/Command** find a surface; **Settings** change a preference.  
9. Kill/reopen → **Continuity** restores session.  
10. Exit Capsule without losing Vault/Care provenance.

Until this journey is evidenced, `GUNNCHOS_PIXEL_FULL_ECOSYSTEM_JOURNEY_PASS` stays **false**.

---

## 10. Core parity matrix (evidence-based summary)

Form factors × domains — classifications from current code, not ambition. Full cell detail: `artifacts/vxp2/reports/GUNNCHOS_FORM_FACTOR_PARITY_MATRIX.json`.

| Domain | Phone/Capsule (Pixel) | Handheld | Student 14.5" | DS-XL Coder | Edge/Wearable |
|--------|----------------------|----------|---------------|-------------|---------------|
| WAIKE | NOT_IMPLEMENTED (launch bridge only) | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | UNAVAILABLE_PLATFORM_LIMIT* |
| gunnchAI | NOT_IMPLEMENTED (launch metadata only) | NOT_IMPLEMENTED | FALLBACK (tutor HTML elsewhere) | FALLBACK | UNAVAILABLE_PLATFORM_LIMIT* |
| Gaming | NOT_IMPLEMENTED (no library surface; matrix stub) | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | UNAVAILABLE_PLATFORM_LIMIT* |
| Creation | NOT_IMPLEMENTED | NOT_IMPLEMENTED | FALLBACK (creator_studio seed) | FALLBACK | UNAVAILABLE_PLATFORM_LIMIT |
| Communication | FULL_VIA_ADAPTER (Connect surface) | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FALLBACK |
| Leisure | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED |
| Vault | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FALLBACK |
| App Center | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FALLBACK |
| Connect | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FALLBACK |
| Assist | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FALLBACK |
| Care | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FALLBACK |
| Wallet | FALLBACK (surface; provider often unavailable) | FALLBACK | FALLBACK | FALLBACK | NOT_IMPLEMENTED |
| Portfolio | FALLBACK | FALLBACK | FALLBACK | FALLBACK | NOT_IMPLEMENTED |
| Career | FALLBACK | FALLBACK | FALLBACK | FALLBACK | NOT_IMPLEMENTED |
| Verifier | FALLBACK | FALLBACK | FALLBACK | FALLBACK | NOT_IMPLEMENTED |
| Search | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED |
| Settings | NOT_IMPLEMENTED (Assist ≠ Settings) | NOT_IMPLEMENTED | FALLBACK (launcher_mock only) | FALLBACK | NOT_IMPLEMENTED |
| Continuity | FALLBACK (SessionStore; Home Continue empty) | FALLBACK | FALLBACK | FALLBACK | FALLBACK |
| Home | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FULL_VIA_ADAPTER | FALLBACK |

\*Wearable may surface glance/status for these domains via Continuity; full interactive routes remain platform-limited unless docked/paired to a primary device.

---

## 11. Explicit non-goals / forbidden identity claims

- No phone-only gunnchOS.  
- No reduced-mobile edition as the Capsule story.  
- No companion-app identity for Android Capsule.  
- No launcher-only identity (Home ≠ app grid).  
- No Apple visual/interaction IP appropriation.  
- No claiming `GUNNCHOS_CAPSULE_EXPERIENCE_PARITY` or universal gates until evidence + owner review.

---

## 12. Owner review checklist (unanswered)

Human gates remain **false** until an owner checks these:

- [ ] Capsule on Pixel reads as the **same gunnchOS**, not a companion or launcher  
- [ ] Shared navigation grammar is recognizable across phone / handheld / 14.5" / coder  
- [ ] Home Continue / context behavior is desirable and honest  
- [ ] WAIKE full-route experience is acceptable for Pixel ecosystem journey  
- [ ] gunnchAI full-route experience is acceptable for Pixel ecosystem journey  
- [ ] Gaming library + return-to-Capsule loop is acceptable  
- [ ] Creation / Communication / Leisure places feel like one product family  
- [ ] Vault, App Center, Care, Connect depth is sufficient for daily use  
- [ ] Search/Command and Settings are present as system surfaces (not buried)  
- [ ] Capability absences show honest limits without deleting identity  
- [ ] Form-factor adapters enhance without forking OS identity  
- [ ] Pixel full ecosystem journey (section 9) completed hands-on  
- [ ] Desire / coherence: “I want to keep using this” passes owner judgment  
- [ ] Merge authorized for this addendum lane  

---

## 13. Related gates

Defined in `artifacts/vxp2/reports/GUNNCHOS_UNIVERSAL_PARITY_GATES.json` (also referenced from `artifacts/vxp/reports/VXP_GATES.json`).

Human / merge gates stay false until checklist above is answered.
