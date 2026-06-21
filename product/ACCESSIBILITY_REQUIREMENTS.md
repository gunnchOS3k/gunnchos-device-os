# Accessibility Requirements

WCAG 2.x and Universal Design for Learning (UDL) aligned requirements for the gunnchOS user-focused OS experience layer.

**Status:** device OS alpha · accessibility-first UX — not certified WCAG conformance or user-tested with participants with disabilities.

---

## 1. Principles

Accessibility is not a bolt-on feature. The experience layer must be:

- **Perceivable** — information presentable in multiple ways
- **Operable** — navigable by keyboard, touch, controller, and assistive tech placeholders
- **Understandable** — plain language, predictable behavior, low cognitive load options
- **Robust** — works across presets, offline, and edge-case fallbacks

Aligned with UDL guidelines:

- Multiple means of **engagement**
- Multiple means of **representation**
- Multiple means of **action and expression**

---

## 2. Supported features

All features below must be configurable via `accessibility_manager.py` and present in `config/accessibility_defaults.yaml`:

| Feature | ID | Requirement |
|---------|-----|-------------|
| Keyboard navigation | `keyboard_navigation` | Full tab order; visible focus; no keyboard traps |
| Controller navigation | `controller_navigation` | D-pad/stick focus movement in Arcade and a11y presets |
| Touch navigation | `touch_navigation` | Targets ≥ 44×44 dp equivalent; spacing for motor limitations |
| Screen reader labels | `screen_reader_labels` | Every interactive element has accessible name |
| Captions preference | `captions_preference` | Default on for media; user override |
| Reduced motion | `reduced_motion` | Respect system/preset; disable non-essential animation |
| High contrast | `high_contrast` | Theme + override; no information by color alone |
| Large text | `large_text` | font_scale override; reflow without horizontal scroll |
| Simplified language | `simplified_language` | Short sentences in Scooter/Bicycle; reading level aware |
| Focus mode | `focus_mode` | Hide non-essential UI chrome in Studio/Workshop |
| Color-safe mode | `color_safe_mode` | Color-blind safe palette tokens |
| Audio cues | `audio_cues` | Optional sounds for confirmations (with mute) |
| Haptic cues | `haptic_cues` | Optional haptics on supported hardware |
| One-hand mode | `one_hand_mode` | Reachable targets; sidebar repositioning |
| Switch access | `switch_access` | Placeholder — scanning UI documented, not production AT |
| Voice input | `voice_input` | Placeholder — must not block other input methods |

`validate_coverage(settings)` must report any missing feature keys.

---

## 3. WCAG alignment matrix

| WCAG principle | gunnchOS requirement | Implementation |
|----------------|---------------------|----------------|
| **1.1 Text alternatives** | Icons have text labels; decorative icons marked | screen_reader_labels on all controls |
| **1.3 Adaptable** | Content order meaningful; no layout-only meaning | Semantic home layout; reflow on large_text |
| **1.4 Distinguishable** | Contrast, resize text, no color-only cues | high_contrast theme; color_safe_mode; large_text |
| **2.1 Keyboard accessible** | All functions via keyboard | keyboard_navigation; focus visible |
| **2.2 Enough time** | No timeouts on Scooter; extendable elsewhere | motor_limitations edge case extends timeouts |
| **2.3 Seizures** | Reduced motion default for youth | reduced_motion in kid_safe, scooter presets |
| **2.4 Navigable** | Skip links, headings, focus order | "Help" and "Home" always reachable |
| **2.5 Input modalities** | Touch, pointer, controller | touch_navigation, controller_navigation |
| **3.1 Readable** | Plain language; reading level | simplified_language; persona reading_level |
| **3.2 Predictable** | Consistent navigation; no surprise context changes | Preset exit paths documented |
| **3.3 Input assistance** | Error messages in plain language | Edge case user_message strings |
| **4.1 Compatible** | Valid labels; status messages | Screen reader labels; offline/a11y cache |

**Not claimed:** formal WCAG 2.1 AA audit or certification.

---

## 4. UDL alignment matrix

| UDL guideline | gunnchOS requirement |
|-------------|---------------------|
| **Engagement — options for recruiting interest** | Persona choice; scooter-to-spaceship; creative presets |
| **Engagement — sustaining effort** | Progress widgets (Bicycle); focus_mode (Studio) |
| **Engagement — self-regulation** | Guardian controls; focus_mode; overwhelmed → scooter fallback |
| **Representation — perception** | high_contrast, large_text, audio_cues, captions |
| **Representation — language** | simplified_language; preferred_language on profile |
| **Representation — comprehension** | Guided onboarding; one primary action per screen |
| **Action — physical action** | touch, keyboard, controller, one_hand_mode, switch_access placeholder |
| **Action — expression** | Multiple app packs; creator workflows; voice placeholder |
| **Action — executive function** | Workspaces with quick_actions; widgets for goals |

---

## 5. Preset-specific accessibility defaults

Each journey preset has defaults in `config/accessibility_defaults.yaml`:

| Preset | Required defaults |
|--------|-------------------|
| Scooter | large_text, simplified_language, reduced_motion, touch_navigation |
| Bicycle | simplified_language, touch_navigation, keyboard_navigation, captions_preference |
| Car | keyboard_navigation, touch_navigation |
| Studio | focus_mode available, color_safe_mode available |
| Arcade | controller_navigation, captions_preference |
| Workshop | keyboard_navigation, high_contrast available |
| Laboratory | keyboard_navigation, screen_reader_labels |
| Spaceship | all features user-configurable |
| Guardian | kid_safe theme option; inherited youth defaults |
| Classroom | teacher can set class-wide a11y profile |
| Library | large_text, high_contrast available, simplified_language |
| Offline | full offline a11y cache; all navigation modes enabled |

Global defaults in `accessibility_defaults.yaml` → `global` key apply to all presets unless overridden.

---

## 6. Inclusive design requirements

### 6.1 Neurodiversity

- Reduced motion and focus_mode reduce sensory load.
- Scooter preset limits choices to prevent overwhelm.
- `overwhelmed` edge case auto-simplifies UI.

### 6.2 Low vision

- high_contrast and large_text themes.
- screen_reader_labels on all controls.
- audio_cues optional for confirmation.

### 6.3 Motor accessibility

- Large touch targets in simple/guided depth.
- controller_navigation and one_hand_mode.
- switch_access placeholder with extended timeouts.
- `cannot_type` edge case enables non-keyboard paths.

### 6.4 Cognitive load

- simplified_language in youth presets.
- One primary action per screen in Scooter.
- "More control" hides advanced settings until requested.

### 6.5 Language access

- `preferred_language` on user profile.
- Reading level aware copy in onboarding.
- Captions default on for media.

### 6.6 Offline and low-bandwidth

- Full a11y settings cached offline.
- No degradation of accessibility features when offline.

---

## 7. Theme accessibility requirements

Every theme in `config/themes.yaml` must include non-empty `accessibility_notes` explaining:

- Who the theme serves
- Contrast considerations
- Motion level impact
- Known limitations

Themes must not rely on color alone for status (error, success, warning).

---

## 8. Launcher and UI requirements

- Every control has an accessible label (not icon-only without aria/name).
- No color-only meaning for app state or alerts.
- Support reduced motion in all animations.
- Support high contrast mode without broken layouts.
- Keyboard/controller/touch navigation notes in UI docs.
- No dead-end screens — always reachable Help and Home.

---

## 9. Accessibility-first persona

The `accessibility_first_user` persona must:

- Default to Scooter or Bicycle with full a11y overrides applied at onboarding.
- Ship with `accessibility_essentials_pack`.
- Offer guided expansion to full customization without forced complexity.
- Success moment: navigate home screen with preferred input method independently.

---

## 10. Testing and validation

| Check | Command / test |
|-------|----------------|
| Feature coverage | `scripts/validate_accessibility_coverage.py` |
| Preset defaults | Every preset has entry in accessibility_defaults.yaml |
| Unit tests | `tests/test_accessibility_manager.py` |
| High contrast, large text, reduced motion | Must appear in demo output |

Validators must fail if any preset lacks accessibility defaults or any SUPPORTED_FEATURE is missing from global config.

---

## 11. Claim boundary

**Allowed:** accessibility-first UX · WCAG/UDL aligned design intent · inclusive defaults per preset

**Not claimed:** certified WCAG conformance · compatibility with all assistive technologies · user testing with disabled participants (until conducted)

See [CLAIM_BOUNDARY.md](CLAIM_BOUNDARY.md).
