# gunnchOS Android Full Experience Gaps

**Status:** VXP-2 addendum — gap-to-project map (post Gate B digital implementation)  
**Governs under:** `docs/product/GUNNCHOS_DEVICE_PARITY_CONTRACT.md`  
**Pixel reference:** Capsule on stock Pixel (`artifacts/android_capsule/GATES.json`)  
**Honesty rule:** Prefer `NOT_IMPLEMENTED` / product gap over false PASS. Human gates remain unanswered.

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
| **current implementation** | Living Workspace + domain routes; contract wording corrected; Settings About states Capsule ≠ companion |
| **Pixel result** | Digital shell identity improved; physical ecosystem journey not re-run this PR (ADB stop) |
| **desired** | Same product family identity as Student/DS-XL; never “companion app” |
| **limitation_type** | product_gap (owner confirmation) |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Owner human gates for identity/desire; complete Pixel §20 journey when ADB free |

### 2. Shared navigation grammar completeness

| | |
|--|--|
| **capability** | Home, Apps, Search/Command, Continuity, Settings |
| **current implementation** | Dock/rail + topbar Search/Settings; Continuity Continue cards; More domains |
| **Pixel result** | Digitally present; viewport overflow not re-captured on device this PR |
| **desired** | Full grammar; presentation adapts |
| **limitation_type** | product_gap (notifications tray still shallow) |
| **responsible_repo** | `gunnchos-device-os` (`apps/gunnch_shell`) |
| **next_action** | Notifications surface depth; form-factor capture pack |

### 3. WAIKE full route

| | |
|--|--|
| **capability** | In-OS WAIKE learning journey |
| **current implementation** | `WaikeSurface` + `WaikeProvider` classified `FULL_VIA_ADAPTER`; offline honesty; return-to-gunnchOS |
| **Pixel result** | Route exists in rebuilt assets; hub URL still owner-configured; physical journey pending |
| **desired** | Full route with continue lesson + offline honesty; PWA adapter OK |
| **limitation_type** | product_gap (+ cross-repo SoR depth) |
| **responsible_repo** | `gunnchos-device-os`; WAIKE Learning Platform SoR |
| **next_action** | Bundle/default hub; deep-link Learning OS when installed; owner accept |

### 4. gunnchAI full route

| | |
|--|--|
| **capability** | Assistant surface on Capsule |
| **current implementation** | `GunnchAiSurface` conversation, provenance, cancel/retry/fallback; truthful runtime labels |
| **Pixel result** | Shell route ready in assets; Nearby Mac pairing still none |
| **desired** | Full ask/help with offline fallback |
| **limitation_type** | product_gap (frontier/remote depth) |
| **responsible_repo** | `gunnchos-device-os`; `gunnchAI3k` |
| **next_action** | Optional remote/nearby pairing without ever labeling Nearby as On-device |

### 5. Gaming library route

| | |
|--|--|
| **capability** | Games library + launch + return |
| **current implementation** | `GamesSurface` + `games_list` / `games_launch`; App Library Games category |
| **Pixel result** | Library UX present; CAPSULE_WEB builds may still be missing under `assets/games/` |
| **desired** | Library + launch modes + return |
| **limitation_type** | product_gap (asset bundling) |
| **responsible_repo** | `gunnchos-device-os`; game repos |
| **next_action** | Bundle web builds or native packages; Continuity already records play |

### 6. Creation route

| | |
|--|--|
| **capability** | Creation domain entry |
| **current implementation** | `CreationSurface` create/edit/save local notes + Continuity |
| **Pixel result** | Usable domain in shell; heavy `creator_studio` still optional escalation |
| **desired** | Creation place with honest tool depth |
| **limitation_type** | product_gap (depth) |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Vault export of notes; camera/pen adapters when present |

### 7. Communication depth

| | |
|--|--|
| **capability** | Connect as Communication domain |
| **current implementation** | Connect usable; telephony status honest (“not available”) |
| **Pixel result** | Shallow local mail/calendar |
| **desired** | Universal Communication place with adapters |
| **limitation_type** | product_gap (depth); telephony may be platform_limitation |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Deepen sync providers when SoR ready |

### 8. Leisure route

| | |
|--|--|
| **capability** | Non-game leisure / media |
| **current implementation** | `LeisureSurface` rights-safe activities; no unlicensed streaming |
| **Pixel result** | Domain present digitally |
| **desired** | Leisure place in product family |
| **limitation_type** | product_gap (catalog depth) |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Local media import polish via Vault |

### 9. Search / Command

| | |
|--|--|
| **capability** | System-wide find |
| **current implementation** | `SearchCommandSurface` wired index only |
| **Pixel result** | Digital route present |
| **desired** | Index only real destinations |
| **limitation_type** | product_gap (Vault file hits when provider down) |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Optional Vault provider hits when reachable — never invent |

### 10. Pixel full ecosystem journey

| | |
|--|--|
| **capability** | Hands-on Pixel §20 journey + contact sheet |
| **current implementation** | Stop documented: Capsule already top-resumed; ADB not seized |
| **Pixel result** | Prior Capsule proofs exist; this PR did not re-traverse |
| **desired** | Evidenced journey under `artifacts/vxp2/pixel/full_ecosystem/` |
| **limitation_type** | process / device ownership |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Re-run when ADB free; keep gate false until then |

### 11. Capability adapters still incomplete

| | |
|--|--|
| **capability** | Camera capture, pen, gamepad, external display adapters |
| **current implementation** | Bridge gates exist for camera/mic; not full adapter UX |
| **Pixel result** | Honest absences in Settings capability summary |
| **desired** | Adapters enhance without forking identity |
| **limitation_type** | product_gap |
| **responsible_repo** | `gunnchos-device-os` |
| **next_action** | Incremental adapter surfaces per capability profile |

---

## Closed or reduced this PR (digital)

- Settings searchable system surface
- Search / Command wired index
- Continuity / Home Continue cards
- WAIKE / gunnchAI / Games / Creation / Leisure shell routes
- App Library category unification
- Engineering metadata moved to Settings → Developer / Diagnostics

## Still false (policy)

All `GUNNCHOS_*` human/owner gates in `artifacts/vxp2/reports/GUNNCHOS_UNIVERSAL_PARITY_GATES.json` remain **false**, including merge authorization.
