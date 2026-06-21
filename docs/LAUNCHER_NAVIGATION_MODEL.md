# Launcher Navigation Model

**Status:** device OS alpha · UX contract for launcher mock  
**Implementation:** `apps/launcher_mock/src/App.tsx`, `apps/launcher_mock/src/user-focused/UserFocusedView.tsx`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Navigation topology

The launcher mock uses a **two-root navigation model**:

```
Root
├── Fleet view (default on load)
│   ├── Campus selector (7GC scenarios)
│   ├── Device selector
│   ├── Mode selector
│   ├── App grid (launch placeholders)
│   └── Info panels (telemetry, privacy, deploy, …)
└── User-focused view
    ├── Tab: Who (persona)
    ├── Tab: Journey (preset)
    ├── Tab: Customize
    ├── Tab: Accessibility
    ├── Tab: Apps (app pack)
    ├── Tab: Home (workspace summary)
    ├── Tab: Guardian
    └── Tab: Offline
```

There is **no deep linking or URL routing** in alpha — view state is in-memory only.

---

## Fleet view flow

1. User lands on fleet view with default campus **Gary**, device **first in DEVICES**, mode **first in MODES**
2. Campus change updates contextual blurb (mode recommendation, privacy, WAIKE track, Edge-IO note)
3. Device + mode change update panel metadata (`deviceId`, `modeId` from maps)
4. App grid buttons are **non-navigating placeholders** (no router)
5. User may switch to user-focused view at any time

**Primary audience:** researchers, fleet admins, demo presenters.

---

## User-focused view flow

### Onboarding path (happy path)

```
Persona (Who) → select persona
    ↓ auto-advance
Journey → confirm or change preset
    ↓ user choice
Customize / Accessibility / Apps → configure
    ↓
Home → review workspace summary
    ↓ optional
Guardian / Offline → safety and connectivity
```

### Tab behavior

| Tab | Entry action | Exit state preserved |
|-----|--------------|---------------------|
| Who | Select persona | Preset updated from persona default |
| Journey | Select preset | Preset ID in state |
| Customize | Theme, depth | theme, depth |
| Accessibility | Toggles | highContrast, largeText, reducedMotion |
| Apps | App pack | appPack ID |
| Home | Read-only summary | — |
| Guardian | Enable toggle | guardian boolean |
| Offline | Enable toggle | offline boolean |

Tabs are **peer navigation** — no forced linear wizard after initial persona pick.

---

## Mode vs journey preset

| Concept | Fleet view | User-focused view | Python source |
|---------|------------|-------------------|---------------|
| **Mode** | OS policy (School, Developer, …) | Indirect via preset/persona | `config/modes.yaml` |
| **Journey preset** | Not shown | Scooter, Car, Spaceship, … | `config/journey_presets.yaml` |

Presets map to complexity and app visibility; modes map to allow/block lists and telemetry policy.

---

## Deploy navigation (fleet panel)

Deploy is **informational + mock action** in fleet view:

- Shows `source: ds_xl_coder → target: {deviceId}`
- Button triggers no backend — real flow documented in `docs/DS_XL_DEPLOY_CONTRACT.md`

---

## Keyboard and focus (alpha intent)

| Area | Behavior |
|------|----------|
| Tab bar | Buttons with `aria-label`, `aria-current` |
| View switch | Fixed-position fleet toggle in user-focused view |
| App grid | Focusable buttons (fleet) |
| Selects | Native `<select>` for campus/device/mode |

Full keyboard map is specified in `LAUNCHER_ACCESSIBILITY_CONTRACT.md`. Production shell would add roving tabindex for app grid.

---

## Future navigation (not claimed)

- Deep links (`gunnchos://mode/school`)
- Back stack for app launches
- Guardian PIN gate before restricted tabs
- Sync with `onboarding_wizard.py` first-run flow

---

## Related documents

- [LAUNCHER_MOCK_ARCHITECTURE.md](LAUNCHER_MOCK_ARCHITECTURE.md)
- [LAUNCHER_COMPONENT_MAP.md](LAUNCHER_COMPONENT_MAP.md)
- [SCOOTER_TO_SPACESHIP_MODEL.md](SCOOTER_TO_SPACESHIP_MODEL.md)
