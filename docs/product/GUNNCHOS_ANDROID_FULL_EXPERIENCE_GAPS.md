# gunnchOS Android Full Experience Gaps

**Status:** VXP-2 addendum — gap-to-project map  
**Governs under:** `docs/product/GUNNCHOS_DEVICE_PARITY_CONTRACT.md`  
**Pixel reference:** Capsule on stock Pixel (`artifacts/android_capsule/GATES.json`)  
**Honesty rule:** Prefer `NOT_IMPLEMENTED` / product gap over false PASS.

---

## How to read

| Field | Meaning |
|-------|---------|
| capability | Product capability or surface |
| current implementation | What exists in code today |
| Pixel result | What a Pixel Capsule user effectively gets |
| desired universal behavior | Contract target |
| limitation_type | `platform_limitation` vs `product_gap` |
| responsible_repo | Primary ownership |
| next_action | Concrete next step |

---

## Gaps

### 1. Universal OS identity (not companion / not reduced)

| | |
|--|--|
| **capability** | Capsule presents as full gunnchOS |
| **current implementation** | Living Workspace shell in WebView; docs historically say experience parity / companion seeds |
| **Pixel result** | Fullscreen Capsule works (`CAPSULE_PIXEL_INTERACTIVE_SHELL_PASS`); aggregate `GUNNCHOS_CAPSULE_EXPERIENCE_PARITY=false` |
| **desired** | Same product family identity as Student/DS-XL; never “companion app” |
| **limitation_type** | product_gap (positioning + incomplete domains) |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Enforce this contract in shell copy + gates; complete domain routes below |

### 2. Shared navigation grammar completeness

| | |
|--|--|
| **capability** | Home, Apps, Search/Command, Continuity, Notifications/Status, Settings |
| **current implementation** | Dock/rail: Home, Vault, App Center, Connect, More→Assist/Care/Wallet/Portfolio/Career/Verifier |
| **Pixel result** | Partial grammar; no Search/Command, Settings, Continuity, Notifications slots |
| **desired** | Full grammar; presentation adapts |
| **limitation_type** | product_gap |
| **responsible_repo** | `gunnchos-device-os` (`apps/gunnch_shell`) |
| **next_action** | Add system Search/Command + Settings surfaces; wire Continuity module on Home; status tray |

### 3. WAIKE full route

| | |
|--|--|
| **capability** | In-OS WAIKE learning journey |
| **current implementation** | `WaikeProvider.launch` → Custom Tab if https URL; else metadata. App Center catalog entry. No shell `waike` surface. Seed HTML in `apps/waike_learning`. SoR: Waike Learning Platform (Tauri). |
| **Pixel result** | Launch bridge only — not a first-class OS route |
| **desired** | Full route with continue lesson + offline honesty; PWA adapter OK |
| **limitation_type** | product_gap (+ cross-repo SoR) |
| **responsible_repo** | `gunnchos-device-os` (shell route + provider); `gunnchAI3k` / Waike Learning Platform (SoR LMS); `waike-research-ops` (curriculum) |
| **next_action** | Add shell WAIKE surface invoking provider; bundle hub URL; deep-link to Learning OS when installed |

### 4. gunnchAI full route

| | |
|--|--|
| **capability** | Assistant surface on Capsule |
| **current implementation** | `GunnchAiProvider.launch` returns JSON flags only; tutor HTML + companion_bridge in device-lab paths; no shell surface |
| **Pixel result** | No in-shell assistant UI |
| **desired** | Full ask/help route with offline fallback |
| **limitation_type** | product_gap |
| **responsible_repo** | `gunnchos-device-os`; `gunnchAI3k` |
| **next_action** | Shell `gunnchai` surface → bridge → local tutor/runtime; retire “launch metadata = PASS” for full-route gate |

### 5. Gaming library route

| | |
|--|--|
| **capability** | Games library + launch + return |
| **current implementation** | `GamesProvider` four-game matrix; App Center lists games; no Games surface in `CompleteExperienceShell` |
| **Pixel result** | No library UX; web assets may be missing under `assets/games/` |
| **desired** | Library surface; CAPSULE_WEB / native / guest modes; return to Capsule |
| **limitation_type** | product_gap |
| **responsible_repo** | `gunnchos-device-os`; game repos (`anime-aggressors`, `pedestrian-pursuit`, `archive-of-life-artifact-world`, `beatlink-party`) |
| **next_action** | Add Games surface; bundle or fetch web builds; gate library route separately from matrix completeness |

### 6. Creation route

| | |
|--|--|
| **capability** | Creation domain entry |
| **current implementation** | `apps/creator_studio` seed; `docs/CREATOR_MODES.md` + Python manager — not in production shell nav |
| **Pixel result** | Not reachable from Living Workspace |
| **desired** | Creation place with honest tool depth |
| **limitation_type** | product_gap |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Shell Creation surface wiring creator modes; camera/pen adapters when present |

### 7. Communication depth

| | |
|--|--|
| **capability** | Connect as Communication domain |
| **current implementation** | `ConnectSurface` local compose/queue + calendar list; `ConnectProvider` on Android |
| **Pixel result** | Usable shallow Connect; not full messaging stack |
| **desired** | Universal Communication place with adapters (telephony optional) |
| **limitation_type** | product_gap (depth); telephony may be platform_limitation for some SKUs |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Keep surface; deepen sync providers; document telephony as enhancement |

### 8. Leisure route

| | |
|--|--|
| **capability** | Non-game leisure / media |
| **current implementation** | None in shell |
| **Pixel result** | Missing |
| **desired** | Leisure place in product family |
| **limitation_type** | product_gap |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Define minimal Leisure surface + offline media policy |

### 9. Vault / App Center / Care (parity polish)

| | |
|--|--|
| **capability** | Daily-driver file, catalog, backup |
| **current implementation** | Surfaces + Android providers; shell also has localhost provider ports for Linux |
| **Pixel result** | Code PASS on capsule gates; physical owner usability still pending for aggregate parity |
| **desired** | Reliable FULL_VIA_ADAPTER daily use |
| **limitation_type** | product_gap (usability/evidence), not absence |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Owner Pixel usability pass; wire shell to Capsule bridge for list/ops when host is ANDROID_CAPSULE |

### 10. Search / Command

| | |
|--|--|
| **capability** | System Search/Command |
| **current implementation** | Per-surface search inputs only |
| **Pixel result** | No system command palette |
| **desired** | Grammar slot always available |
| **limitation_type** | product_gap |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Implement Search/Command surface + shortcut |

### 11. Settings

| | |
|--|--|
| **capability** | System Settings |
| **current implementation** | Assist = a11y contrast/motion/scale; `launcher_mock` SettingsPanel not production |
| **Pixel result** | No Settings surface |
| **desired** | Settings as grammar slot; Assist remains a11y module |
| **limitation_type** | product_gap |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Promote Settings surface; nest Assist entry |

### 12. Continuity

| | |
|--|--|
| **capability** | Resume / handoff |
| **current implementation** | `SessionStore` + `session_get`/`session_put`; Home Continue always empty-honest |
| **Pixel result** | Session may persist natively; Home does not surface resume cards |
| **desired** | Continue module populated from real sessions |
| **limitation_type** | product_gap |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Bind Home Continue to SessionStore; cross-device later |

### 13. Camera / mic capture UX

| | |
|--|--|
| **capability** | Media capture adapters |
| **current implementation** | Permission stubs; `capture_started: false` |
| **Pixel result** | Consent check only |
| **desired** | Creation/Care capture when granted |
| **limitation_type** | product_gap (API present, UX not) |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Intent-launch capture + return URI into Vault |

### 14. Linux guest / desktop in Capsule

| | |
|--|--|
| **capability** | Guest desktop for coder/games |
| **current implementation** | `LinuxGuestProvider`; QEMU/AVF probes |
| **Pixel result** | `CAPSULE_QEMU_GUEST_BOOT_PASS=false` |
| **desired** | Optional guest mode when earned |
| **limitation_type** | platform_limitation + product_gap |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Keep UNAVAILABLE_PLATFORM_LIMIT until guest boot earned; do not block phone identity |

### 15. Wallet / Portfolio / Career / Verifier providers

| | |
|--|--|
| **capability** | Credential spine |
| **current implementation** | Shell surfaces; providers often unreachable → honest unavailable |
| **Pixel result** | UI shells with empty/unavailable |
| **desired** | Working local providers or clear offline vault-backed mode |
| **limitation_type** | product_gap |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Ship Capsule-local providers or bridge to existing CX providers |

### 16. Edge IO / wearable coherence

| | |
|--|--|
| **capability** | Wearable/edge as family adapters |
| **current implementation** | Device-class docs; measurement node sibling repo; Capsule bluetooth metadata only |
| **Pixel result** | No wearable Continuity module |
| **desired** | Sensors enhance Care/Continuity without forking OS |
| **limitation_type** | product_gap |
| **responsible_repo** | `gunnchos-device-os`; `edge-io-measurement-node`; hardware design repos |
| **next_action** | Define Continuity glance contract; pair when hardware present |

### 17. Pixel full ecosystem journey evidence

| | |
|--|--|
| **capability** | End-to-end journey §9 of parity contract |
| **current implementation** | Partial physical proofs (Home render, interactive shell) |
| **Pixel result** | Journey incomplete → gate false |
| **desired** | Documented hands-on pass |
| **limitation_type** | product_gap (evidence) |
| **responsible_repo** | `gunnchos-device-os` (owner) |
| **next_action** | Run checklist; attach artifacts under `artifacts/vxp2/` |

---

## Top gaps (priority)

1. WAIKE + gunnchAI + Games **first-class shell routes** (`gunnchos-device-os` + Waike/gunnchAI/game repos).  
2. Search/Command + Settings grammar slots (`gunnchos-device-os`).  
3. Home Continuity wired to SessionStore (`gunnchos-device-os`).  
4. Creation + Leisure places (`gunnchos-device-os`).  
5. Owner Pixel ecosystem journey + human coherence gates (owner).

---

## Explicitly not “Android reduced”

Closing gaps must expand Capsule toward **universal** gunnchOS. Do not resolve gaps by declaring phone a companion or by deleting domains.
