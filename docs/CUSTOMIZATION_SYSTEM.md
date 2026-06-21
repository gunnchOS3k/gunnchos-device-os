# Customization System

**Status:** device OS alpha · customization framework — not production-polished themes  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## 1. Design intent

Users choose **how much control** they want. A pre-K learner on Scooter sees essential choices only; a postdoctoral researcher on Spaceship sees advanced panels, export/import, and power-user settings.

Customization must never block safe defaults. Guardian and accessibility overrides take precedence over cosmetic choices.

---

## 2. Customization depth levels

From `product/CUSTOMIZATION_REQUIREMENTS.md` and `UserProfile.customization_depth`:

| Depth | Settings view | Typical preset / persona |
|-------|---------------|--------------------------|
| `simple` | Essential only — theme preset, text size, help | Scooter, pre_k_learner, library user |
| `guided` | Step-by-step with explanations | Bicycle, middle school, accessibility-first |
| `full` | Common settings visible | Car, Studio, most adults |
| `power_user` | Advanced panels, JSON import/export | Spaceship, Workshop, software_engineer |

The `CustomizationEngine.set_settings_view()` adjusts which settings categories appear in the shell (mock today).

---

## 3. CustomizationEngine API

**Module:** `gunnchos_device_os/customization_engine.py`

| Method | Behavior | Evidence today |
|--------|----------|----------------|
| `change_theme(theme_id)` | Apply theme from `config/themes.yaml` | Python dict returned |
| `change_font_scale(scale)` | Adjust font_scale on active theme | Config merge |
| `change_contrast(mode)` | Set contrast_mode | Config merge |
| `change_home_layout(layout)` | icon_row, grid, workspace_centric | Layout id stored |
| `pin_app` / `unpin_app` | Home screen shortcuts | In-memory list |
| `choose_widgets(widgets)` | Dashboard widgets | In-memory list |
| `set_input_method(method)` | keyboard, touch, controller, … | Profile field update |
| `export_profile()` | JSON snapshot | File-serializable dict |
| `import_profile(data)` | Restore from export | Validates schema fields |
| `reset_to_safe_defaults()` | Persona + preset defaults | Clears pins/widgets |

**Not claimed:** Visual theme rendering in launcher mock for all themes; pixel-polished design system.

---

## 4. Themes

**Module:** `gunnchos_device_os/theme_manager.py`  
**Config:** `config/themes.yaml`

| Theme ID | Intended use |
|----------|--------------|
| `default` | Balanced contrast |
| `kid_safe` | Warm, low-stimulus (Scooter, Guardian) |
| `high_contrast` | Accessibility-first |
| `artist_canvas` | Studio / art_table |
| `writer_focus` | Minimal chrome for writing |
| `musician_studio` | Dark, low-glare |
| `research_terminal` | Laboratory / Spaceship |

Themes include tokens: `background`, `foreground`, `accent`, `font_scale`, `contrast_mode`, `motion_level`.

---

## 5. Layouts and widgets

Home layouts are preset-driven (`journey_preset_engine`) with user overrides via `CustomizationEngine`:

| Layout | Presets using it |
|--------|------------------|
| Single icon row | Scooter |
| Two-row + progress widget | Bicycle |
| 2×4 app grid + homework widgets | Car |
| Workspace-centric | Studio |
| Controller-first arcade | Arcade |
| Dev lab split | Workshop, Spaceship |

Widgets (homework_due, progress_tracker, offline_status, …) are defined per persona in `config/personas.yaml` and per preset in journey config.

---

## 6. Profile import / export

**Use cases:**

- Move settings to a new device (planned).
- Teacher deploys a class template (placeholder).
- Researcher backs up Spaceship configuration.

**Format:** JSON matching `UserProfile.to_dict()` plus customization engine state (pinned apps, widgets, theme_id).

**Gap:** No encrypted transport or cloud sync — local file only in alpha.

---

## 7. Persona-driven defaults

Each persona in `config/personas.yaml` specifies:

- `customization_level` (simple / guided / full)
- `default_widgets`
- `default_app_pack`
- `onboarding_copy` and `recommended_next_step`

Onboarding wizard sets initial depth from user answer to "simple, guided, or full control?"

---

## 8. Safety boundaries

| Rule | Implementation |
|------|----------------|
| Guardian-required personas | Cannot disable content filter via customization alone |
| Scooter preset | Cannot expose terminal or unrestricted browser via pin |
| Accessibility overrides | high_contrast, large_text persist across theme changes |
| reset_to_safe_defaults | Returns to persona + preset, not factory wipe |

---

## 9. Validation

- `scripts/validate_user_focused_os.py` — persona → preset → pack → workspace chain
- Theme IDs must exist in `config/themes.yaml` (manual check today)

**Planned:** pytest for import/export round-trip.

---

## 10. Related documents

- [SCOOTER_TO_SPACESHIP_MODEL.md](SCOOTER_TO_SPACESHIP_MODEL.md)
- [ACCESSIBILITY_AND_INCLUSION.md](ACCESSIBILITY_AND_INCLUSION.md)
- `product/CUSTOMIZATION_REQUIREMENTS.md`
