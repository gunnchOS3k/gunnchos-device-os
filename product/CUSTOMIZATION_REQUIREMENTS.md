# Customization Requirements

Requirements for theme, layout, and profile customization in the gunnchOS user-focused OS experience layer.

**Status:** device OS alpha · customization framework — not a finished shipping OS.

---

## 1. Goals

Users must be able to personalize their device without forced complexity:

- Beginners get simple, safe defaults (Scooter).
- Power users get full control (Spaceship).
- Customizations persist across sessions via profile export/import.
- Reset to safe defaults is always one tap away.

---

## 2. Customization depth levels

| Level | Settings view | Who | Requirements |
|-------|---------------|-----|--------------|
| `simple` | Essential only: theme preset, text size | Scooter, pre-K | Hide advanced panels; max 3 customization choices on screen |
| `guided` | Step-by-step with explanations | Bicycle, middle school | Tooltips on every setting; "Why this matters" copy |
| `full` | All common settings visible | Car, Studio, most adults | Theme, layout, widgets, pins, input method |
| `power_user` | Advanced panels, JSON export | Spaceship, developers | Full export/import; performance overrides; debug placeholders |

Controlled by `customization_depth` on user profile and `CustomizationEngine.set_settings_view()`.

---

## 3. Theme requirements

### 3.1 Required themes (11)

| Theme ID | Purpose | Key tokens |
|----------|---------|------------|
| `default` | Balanced everyday use | Standard contrast, medium icons |
| `high_contrast` | Low vision, bright environments | High contrast mode, large icons |
| `low_light` | Evening, reduced eye strain | Dim palette, warm tones |
| `dyslexia_friendly` | Reading difficulty | Open-dyslexic-style font placeholder, increased spacing |
| `large_text` | Low vision, aging eyes | font_scale ≥ 1.25 |
| `artist_canvas` | Creative work | Neutral background, color-accurate tokens |
| `writer_focus` | Long-form writing | Minimal chrome, distraction-free |
| `musician_studio` | Audio work | Dark studio palette, meter-friendly contrast |
| `gamer_arcade` | Play sessions | Vibrant accents, controller-friendly targets |
| `researcher_terminal` | Lab/terminal work | Monospace-friendly, high information density |
| `kid_safe` | Youth profiles | Rounded icons, no alarming colors, simplified labels |

### 3.2 Theme fields (each theme)

Every theme in `config/themes.yaml` must define:

| Field | Type | Requirement |
|-------|------|-------------|
| `font_scale` | float | 0.85–2.0; default 1.0 |
| `contrast_mode` | string | `standard`, `high`, `low_light` |
| `color_tokens` | dict | Named semantic tokens (background, foreground, accent, error, success) |
| `motion_level` | string | `normal`, `reduced`, `none` |
| `icon_size` | string | `small`, `medium`, `large`, `extra_large` |
| `reading_density` | string | `compact`, `comfortable`, `spacious` |
| `accessibility_notes` | list | Non-empty; explain who benefits |

### 3.3 Theme operations

| Operation | API | Requirement |
|-----------|-----|-------------|
| List themes | `theme_manager.list_themes()` | Return all 11 theme IDs |
| Get theme | `theme_manager.get_theme(id)` | Return full theme dict |
| Apply theme | `customization_engine.change_theme(id)` | Update active theme; return applied tokens |
| Change font scale | `customization_engine.change_font_scale(scale)` | Override theme default; persist in profile |
| Change contrast | `customization_engine.change_contrast(mode)` | Override theme default; persist in profile |

Themes must not use color-only meaning. Every state must have icon + text label.

---

## 4. Layout requirements

### 4.1 Home layout options

| Layout | Preset association | Specification |
|--------|-------------------|---------------|
| Icon row (minimal) | Scooter | 3–4 large icons, single row |
| Guided grid | Bicycle | 2×3 grid + one widget row |
| Productivity grid | Car | 2×4 grid + widget column |
| Workspace-centric | Studio, Workshop, Laboratory | Workspace fills center; apps in sidebar |
| Game shelf | Arcade | Large tiles, horizontal scroll |
| Full grid | Spaceship | Standard grid + dock |

### 4.2 Pin and widget management

| Operation | API | Requirement |
|-----------|-----|-------------|
| Pin app | `customization_engine.pin_app(app_id)` | Add to pinned list; respect preset allowed_apps |
| Unpin app | `customization_engine.unpin_app(app_id)` | Remove from pinned list |
| Choose widgets | `customization_engine.choose_widgets(list)` | Only show widgets valid for current preset |
| Change layout | `customization_engine.change_home_layout(layout)` | Validate against customization_depth |

Pinned apps must not bypass preset `blocked_apps` or guardian approval.

---

## 5. Input method requirements

| Input | Requirement |
|-------|-------------|
| Touch | Default; large targets in simple/guided depth |
| Keyboard | Full keyboard navigation; visible focus rings |
| Controller | Arcade and accessibility presets; remapping placeholder |
| Voice | Placeholder; must not block touch/keyboard fallback |
| Switch access | Placeholder; extended timeouts in motor_limitations edge case |

Set via `customization_engine.set_input_method(method)`; stored in `profile.input_preferences`.

---

## 6. Profile import/export requirements

### 6.1 Export format

`customization_engine.export_profile()` returns JSON with:

```json
{
  "profile": { "...UserProfile fields..." },
  "pinned_apps": ["..."],
  "widgets": ["..."],
  "theme_id": "default",
  "settings_view": "simple",
  "available_themes": ["..."]
}
```

### 6.2 Import rules

| Rule | Requirement |
|------|-------------|
| Validation | Reject corrupted JSON; trigger `corrupted_profile` edge case |
| Persona preservation | Import persona and journey_preset if valid |
| Safety | Re-apply guardian controls if `guardian_required: true` |
| Blocked apps | Re-enforce preset blocked_apps after import |
| Theme | Apply theme if ID exists; else default |

### 6.3 Reset to safe defaults

`customization_engine.reset_to_safe_defaults()` must:

- Set `customization_depth` to `simple`
- Set `privacy_level` to `standard`
- Clear pinned apps and widgets
- Apply `default` theme
- Return user message: "Reset to safe defaults"
- Never delete user_id or display_name

---

## 7. Persona-specific customization levels

From `config/personas.yaml` — each persona has `customization_level`:

| Persona category | Typical level |
|------------------|---------------|
| Pre-K, early reader | simple |
| Middle school | guided |
| High school, college, creators | full |
| Software engineer, postdoc, 6G researcher | power_user |
| Library guest | simple (locked) |
| Accessibility-first | guided (expandable) |

---

## 8. UI principles

- One clear primary action per customization screen.
- Advanced settings behind "More control" — never forced on Scooter users.
- Every control has an accessible label.
- Preview theme changes before apply.
- No dead-end screens — always offer "Keep current" or "Undo".

---

## 9. Configuration sources

| File | Content |
|------|---------|
| `config/themes.yaml` | All 11 themes |
| `config/personas.yaml` | Per-persona customization_level |
| `config/journey_presets.yaml` | Layout constraints per preset |

---

## 10. Validation rules

Validators must fail if:

- Any required theme is missing required fields
- Any theme lacks non-empty `accessibility_notes`
- Export/import round-trip loses required profile fields
- Reset does not restore safe defaults
- Customization allows bypass of guardian blocked_apps
