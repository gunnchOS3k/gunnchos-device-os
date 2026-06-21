# Edge Case Requirements

Requirements for exceptional situations in the gunnchOS user-focused OS experience layer. Every edge case must produce:

1. **User-friendly message** — plain language, no jargon
2. **Safe fallback** — journey preset or mode to restore usability
3. **Technical log** — structured entry for diagnostics (may include `{placeholders}`)
4. **Next action** — what the system or user should do next

**Status:** device OS alpha — policy definitions with placeholder implementations where noted.

---

## 1. User capability edge cases

### 1.1 `cannot_read_yet`

| Field | Requirement |
|-------|-------------|
| Trigger | Pre-K user, pre-literate profile, or explicit "I can't read yet" in onboarding |
| User message | "No reading needed! Tap the pictures to start." |
| Safe fallback | `scooter` |
| Technical log | `edge_case:cannot_read_yet profile={user_id}` |
| Next action | Enable icon-only navigation, audio cues, simplified_language, kid_safe theme |

### 1.2 `cannot_type`

| Field | Requirement |
|-------|-------------|
| Trigger | Motor limitation, young age, or voice/touch-only preference |
| User message | "You can tap, speak, or use a controller instead of typing." |
| Safe fallback | `scooter` or `bicycle` |
| Technical log | `edge_case:cannot_type input_prefs={input_preferences}` |
| Next action | Enable touch_navigation, voice_input placeholder, controller_navigation; hide keyboard-required flows |

### 1.3 `low_vision`

| Field | Requirement |
|-------|-------------|
| Trigger | Accessibility need declared or system high-contrast request |
| User message | "We've made text bigger and colors clearer. You can change more in Settings." |
| Safe fallback | Current preset with a11y overlay |
| Technical log | `edge_case:low_vision preset={preset_id}` |
| Next action | Apply high_contrast theme, large_text, screen_reader_labels; offer audio_cues |

### 1.4 `motor_limitations`

| Field | Requirement |
|-------|-------------|
| Trigger | Declared accessibility need or switch-access request |
| User message | "Let's set up controls that work best for you." |
| Safe fallback | `scooter` with extended timeouts |
| Technical log | `edge_case:motor_limitations needs={accessibility_needs}` |
| Next action | Enable switch_access placeholder, one_hand_mode, controller_navigation; increase tap targets |

---

## 2. Environment edge cases

### 2.1 `offline`

| Field | Requirement |
|-------|-------------|
| Trigger | No network connectivity detected |
| User message | "You're offline. These apps still work — we'll sync when you're back online." |
| Safe fallback | `offline` |
| Technical log | `edge_case:offline last_online={timestamp}` |
| Next action | Switch to offline-capable apps; queue sync; show offline_status widget |

### 2.2 `public_shared_device`

| Field | Requirement |
|-------|-------------|
| Trigger | Library mode, kiosk flag, or guest profile |
| User message | "This is a shared device. Your session will reset when you finish." |
| Safe fallback | `library` |
| Technical log | `edge_case:public_shared_device session={session_id}` |
| Next action | Enable session timer; block personal cloud sync; wipe on exit |

---

## 3. User preference edge cases

### 3.1 `overwhelmed`

| Field | Requirement |
|-------|-------------|
| Trigger | User selects "Too much" or rapid preset switching |
| User message | "Let's simplify. Here are just a few choices." |
| Safe fallback | `scooter` |
| Technical log | `edge_case:overwhelmed from_preset={preset_id}` |
| Next action | Reduce visible apps to 3; hide widgets; set customization_depth to simple |

### 3.2 `no_ai`

| Field | Requirement |
|-------|-------------|
| Trigger | User disables AI tutor features |
| User message | "AI tutor is off. You can still use lessons and apps without it." |
| Safe fallback | Current preset minus gunnchAI3k |
| Technical log | `edge_case:no_ai profile={user_id}` |
| Next action | Block gunnchAI3k; keep WAIKE Offline and non-AI apps |

### 3.3 `no_telemetry`

| Field | Requirement |
|-------|-------------|
| Trigger | User or guardian disables telemetry |
| User message | "We won't send usage data. Some features may need manual updates." |
| Safe fallback | Current preset |
| Technical log | `edge_case:no_telemetry consent=denied` |
| Next action | Disable all telemetry export; keep local logs only |

### 3.4 `only_games`

| Field | Requirement |
|-------|-------------|
| Trigger | User selects games-only goal in onboarding |
| User message | "Game time! Pick a game to play." |
| Safe fallback | `arcade` |
| Technical log | `edge_case:only_games age_band={age_band}` |
| Next action | Apply guardian play windows if youth; show game_room workspace |

### 3.5 `only_school`

| Field | Requirement |
|-------|-------------|
| Trigger | School policy or user selects school-only |
| User message | "School mode is on. Learning apps are ready." |
| Safe fallback | `car` or `classroom` |
| Technical log | `edge_case:only_school policy=school_safe` |
| Next action | Block steam and unrestricted browser; enable school_safe network |

### 3.6 `hardcore_developer`

| Field | Requirement |
|-------|-------------|
| Trigger | power_user customization_depth or explicit developer request |
| User message | "Developer tools unlocked. Full terminal and settings available." |
| Safe fallback | `spaceship` |
| Technical log | `edge_case:hardcore_developer skill={skill_level}` |
| Next action | Enable vscode, terminal, wsl_ubuntu; show advanced settings |

---

## 4. Profile and lifecycle edge cases

### 4.1 `child_to_adult_switch`

| Field | Requirement |
|-------|-------------|
| Trigger | Age band upgrade or guardian releases controls |
| User message | "You're growing up! Let's update your device together." |
| Safe fallback | `bicycle` or `car` (guided transition) |
| Technical log | `edge_case:child_to_adult_switch from={old_band} to={new_band}` |
| Next action | Run transition wizard; migrate apps; relax guardian overlay with consent |

### 4.2 `guardian_lockout`

| Field | Requirement |
|-------|-------------|
| Trigger | Guardian PIN/biometric failure threshold exceeded |
| User message | "Guardian unlock needed. Ask your guardian for help." |
| Safe fallback | `guardian` (locked) |
| Technical log | `edge_case:guardian_lockout attempts={count}` |
| Next action | Lock preset changes; allow emergency_unlock_path; log audit event |

### 4.3 `lost_device`

| Field | Requirement |
|-------|-------------|
| Trigger | Device marked lost via fleet/guardian (placeholder) |
| User message | "This device has been reported lost. Contact support." |
| Safe fallback | Locked screen |
| Technical log | `edge_case:lost_device device={device_id}` |
| Next action | Disable local profiles; show contact info; placeholder remote wipe |

### 4.4 `corrupted_profile`

| Field | Requirement |
|-------|-------------|
| Trigger | Profile JSON fails validation on load |
| User message | "Something went wrong with your settings. We've restored safe defaults." |
| Safe fallback | `scooter` with default profile |
| Technical log | `edge_case:corrupted_profile user={user_id} error={validation_errors}` |
| Next action | reset_to_safe_defaults; preserve backup if available |

### 4.5 `first_boot_failure`

| Field | Requirement |
|-------|-------------|
| Trigger | Onboarding wizard fails or config missing |
| User message | "Setup didn't finish. Let's try again with simple defaults." |
| Safe fallback | `scooter` with guest profile |
| Technical log | `edge_case:first_boot_failure reason={error}` |
| Next action | Retry onboarding; load fallback config; never dead-end screen |

---

## 5. Resource edge cases

### 5.1 `storage_almost_full`

| Field | Requirement |
|-------|-------------|
| Trigger | Storage below threshold (e.g., 10% free) |
| User message | "Storage is almost full. Free up space to keep working smoothly." |
| Safe fallback | Current preset (degraded) |
| Technical log | `edge_case:storage_almost_full free_bytes={free}` |
| Next action | Show storage manager; suggest cache clear; block large downloads |

### 5.2 `battery_low`

| Field | Requirement |
|-------|-------------|
| Trigger | Battery below threshold |
| User message | "Battery is low. Saving your work and reducing background activity." |
| Safe fallback | Current preset with power save |
| Technical log | `edge_case:battery_low percent={level}` |
| Next action | Enable efficiency performance profile; prompt save; reduce animations |

---

## 6. Application edge cases

### 6.1 `app_launch_failure`

| Field | Requirement |
|-------|-------------|
| Trigger | App fails to start |
| User message | "That app didn't open. Try again or pick another app." |
| Safe fallback | Current preset home screen |
| Technical log | `edge_case:app_launch_failure app={app_id} error={error}` |
| Next action | Offer retry; suggest alternative app; never blank screen |

### 6.2 `unsafe_app_request`

| Field | Requirement |
|-------|-------------|
| Trigger | User requests blocked or restricted app |
| User message | "This app isn't available in your current mode. Ask a guardian or switch mode if needed." |
| Safe fallback | Current preset |
| Technical log | `edge_case:unsafe_app_request app={app_id} preset={preset_id}` |
| Next action | Show why blocked; offer guardian approval path or preset exit |

### 6.3 `media_app_unsupported`

| Field | Requirement |
|-------|-------------|
| Trigger | Netflix/Hulu/other media not available via supported route |
| User message | "This streaming service isn't set up on this device yet. Try the browser or another app." |
| Safe fallback | Current preset |
| Technical log | `edge_case:media_app_unsupported app={app_id}` |
| Next action | Do not claim DRM bypass; route to official browser if policy allows |

### 6.4 `steam_unavailable`

| Field | Requirement |
|-------|-------------|
| Trigger | Steam not installed, licensed, or compatible |
| User message | "Steam isn't available right now. You can play offline games instead." |
| Safe fallback | `arcade` (offline games only) or `offline` |
| Technical log | `edge_case:steam_unavailable reason={reason}` |
| Next action | Do not claim Steam compatibility guarantee; offer scaly_wings_edu |

### 6.5 `wsl_unavailable`

| Field | Requirement |
|-------|-------------|
| Trigger | WSL not installed or Windows-first strategy not applicable |
| User message | "Linux tools aren't set up yet. You can still code with local tools." |
| Safe fallback | `workshop` (local tools only) |
| Technical log | `edge_case:wsl_unavailable platform={platform}` |
| Next action | Offer vscode local; document Windows-first / WSL-compatible strategy gap |

---

## 7. Implementation requirements

| Requirement | Detail |
|-------------|--------|
| Handler | `edge_case_policy.handle_edge_case(case_id, context)` |
| Config | `config/edge_cases.yaml` — all cases above with required fields |
| Unknown cases | Default to scooter fallback with generic user message |
| No dead ends | Every response includes `next_action` |
| Logging | Technical logs must not include PII in user-visible output |
| Testing | `tests/test_edge_case_policy.py` verifies all cases return four fields |

---

## 8. Validation rules

Validators must fail if:

- Any listed edge case is missing from `config/edge_cases.yaml`
- Any case lacks `user_message`, `safe_fallback`, `technical_log`, or `next_action`
- Any fallback preset ID is invalid
- Docs claim edge cases are user-tested without evidence
