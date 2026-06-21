# User-Focused Launcher Modules

**Status:** device OS alpha · React components for scooter-to-spaceship UX  
**Parent:** [apps/launcher_mock/README.md](../../README.md)

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Purpose

This folder implements the **user-focused gunnchOS experience** in the launcher mock: persona selection, journey presets, customization, accessibility, app packs, workspace home, guardian, and offline panels.

Python counterparts live in `gunnchos_device_os/` (`persona_engine.py`, `journey_preset_engine.py`, `customization_engine.py`, `accessibility_manager.py`, `app_pack_manager.py`, `guardian_controls.py`, `offline_mode_manager.py`).

---

## Files

| File | Role |
|------|------|
| `UserFocusedView.tsx` | Tab shell; lifts shared state |
| `PersonaSelector.tsx` | 22 persona cards |
| `JourneyPresetSelector.tsx` | Scooter → Spaceship presets + UI depth |
| `CustomizationPanel.tsx` | Theme and complexity depth |
| `AccessibilityPanel.tsx` | Large text, high contrast, reduced motion |
| `AppPackSelector.tsx` | App pack picker + `APP_PACKS` constant |
| `WorkspaceHome.tsx` | Summary dashboard |
| `GuardianPanel.tsx` | Mock guardian toggle |
| `OfflineModePanel.tsx` | Mock offline toggle |
| `personaData.ts` | Persona definitions |
| `presetData.ts` | Preset IDs and metadata |

---

## State model

All state is held in `UserFocusedView.tsx`:

```typescript
persona: PersonaId
preset: PresetId
depth: 'simple' | 'guided' | 'full' | 'power_user'
theme: string
highContrast, largeText, reducedMotion: boolean
appPack: string
guardian, offline: boolean
```

Selecting a persona calls `onPersonaSelect` → sets preset from persona default → navigates to Journey tab.

---

## Tab order

1. **Who** — persona  
2. **Journey** — preset  
3. **Customize** — theme/depth  
4. **Accessibility** — a11y toggles  
5. **Apps** — app pack  
6. **Home** — summary  
7. **Guardian** — family safety mock  
8. **Offline** — offline-first mock  

Navigation uses `aria-current="page"` on the active tab.

---

## Config parity

| TS module | YAML config |
|-----------|-------------|
| `personaData.ts` | `config/personas.yaml` |
| `presetData.ts` | `config/journey_presets.yaml` |
| `APP_PACKS` in AppPackSelector | `config/app_packs.yaml` |

Run validation from repo root:

```bash
PYTHONPATH=. python scripts/validate_persona_coverage.py
PYTHONPATH=. python scripts/validate_user_focused_os.py
```

---

## Accessibility

Global styles react to parent state:

- `largeText` → `fontSize: 1.25rem`
- `highContrast` → black background, white text

See [docs/LAUNCHER_ACCESSIBILITY_CONTRACT.md](../../../docs/LAUNCHER_ACCESSIBILITY_CONTRACT.md).

---

## Demos

- [demo/user_focused_os_walkthrough.md](../../../demo/user_focused_os_walkthrough.md)
- [demo/scooter_to_spaceship_walkthrough.md](../../../demo/scooter_to_spaceship_walkthrough.md)

```bash
PYTHONPATH=. python scripts/run_user_focused_os_demo.py
```

---

## Limitations

- No persistence (refresh resets state)
- Guardian/offline toggles do not call Python APIs
- Not all 22 personas have unique visual assets
