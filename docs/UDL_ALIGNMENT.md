# UDL Alignment

**Status:** design intent alignment with Universal Design for Learning — not a UDL certification  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

Universal Design for Learning (UDL) provides a framework for flexible learning environments. gunnchOS maps UDL guidelines to journey presets, personas, and accessibility features.

**Not claimed:** CAST UDL certification, curriculum alignment audit, or classroom efficacy study.

---

## 1. UDL framework overview

UDL organizes recommendations into three principles, each with three guidelines:

1. **Engagement** — the why of learning  
2. **Representation** — the what of learning  
3. **Action & Expression** — the how of learning  

This document maps each guideline to concrete gunnchOS artifacts.

---

## 2. Engagement

### 1.1 Recruit interest

| UDL checkpoint | gunnchOS implementation | Preset / persona |
|----------------|-------------------------|------------------|
| Optimize individual choice | Persona selection in onboarding; pin apps | All |
| Optimize relevance | Persona onboarding_copy; recommended_next_step | Per persona in personas.yaml |
| Minimize threats | Guardian defaults; school-safe browser; no surprise mode switches | Guardian, School, Scooter |
| Choice of complexity | Scooter → Spaceship model | Journey presets |

### 1.2 Sustain effort and persistence

| UDL checkpoint | gunnchOS implementation |
|----------------|-------------------------|
| Goals and feedback | Bicycle progress_tracker, daily_goal widgets |
| Focus on goals | Studio focus_mode; writer essay_studio workspace |
| Collaboration | collaboration placeholders in creator workflows |
| Mastery-oriented | WAIKE lesson progress; homework_tracker widget |

### 1.3 Self-regulation

| UDL checkpoint | gunnchOS implementation |
|----------------|-------------------------|
| Expectations | Preset onboarding text; exit paths documented |
| Support planning | Calendar, homework widgets (Car) |
| Self-assessment | gunnchAI3k tutor sessions (mock, no PII) |
| Personal coping | overwhelmed_user → Scooter fallback; focus_mode |

---

## 3. Representation

### 2.1 Perception

| UDL checkpoint | gunnchOS feature |
|----------------|------------------|
| Customize display | large_text, high_contrast, color_safe_mode, themes |
| Alternatives for audio | captions_preference, audio_cues (optional) |
| Alternatives for visual | screen_reader_labels; text labels on icons |
| Discernible media | reduced_motion; no essential info by color alone |

### 2.2 Language and symbols

| UDL checkpoint | gunnchOS feature |
|----------------|------------------|
| Clarify vocabulary | simplified_language (Scooter/Bicycle) |
| Clarify syntax | Short onboarding strings |
| Support decoding | read_aloud_placeholder (early_reader persona) |
| Promote understanding | gunnchAI3k plain-language tutor (mock) |

### 2.3 Comprehension

| UDL checkpoint | gunnchOS feature |
|----------------|------------------|
| Activate background | WAIKE offline lessons |
| Highlight patterns | Progress widgets |
| Guide information processing | Guided customization depth |
| Maximize transfer | Workspace quick_actions per task |

---

## 4. Action and expression

### 3.1 Physical action

| UDL checkpoint | gunnchOS feature |
|----------------|------------------|
| Vary methods of response | Touch, keyboard, controller, voice placeholder |
| Optimize access to tools | App packs; one-tap Scooter icons |
| Assistive technologies | switch_access placeholder; screen_reader_labels |
| Motor access | one_hand_mode; large targets; motor_limitations edge case |

### 3.2 Expression and communication

| UDL checkpoint | gunnchOS feature |
|----------------|------------------|
| Compose with media | Creator modes: art, write, music |
| Multiple media | sketch, write, music_notes placeholders |
| Build fluencies | Scratch placeholder (middle school) |
| Executive function supports | Workspaces with quick_actions |

### 3.3 Executive functions

| UDL checkpoint | gunnchOS feature |
|----------------|------------------|
| Guide goal-setting | Onboarding goal question |
| Support planning | homework_tracker, calendar_widget |
| Facilitate managing info | App packs group related tools |
| Enhance capacity for monitoring | Guardian dashboard workspace (mock) |

---

## 5. Preset × UDL emphasis

| Journey preset | Primary UDL emphasis |
|----------------|---------------------|
| Scooter | Representation (perception, language); Engagement (minimize threats) |
| Bicycle | Engagement (sustain effort); Action (guided expression) |
| Car | Action (executive function); Engagement (choice) |
| Studio | Action (expression); Engagement (focus) |
| Arcade | Engagement (recruit interest); Action (physical — controller) |
| Workshop | Action (expression, tools); Representation (comprehension) |
| Laboratory | Action (tools); Representation (multiple data views) |
| Spaceship | All three — user-configured |
| Guardian | Engagement (self-regulation via limits) |
| Offline | Representation (cached content); robust access |

---

## 6. Persona × UDL highlights

| Persona | UDL focus |
|---------|-----------|
| pre_k_learner | Engagement 1.1, Representation 2.1–2.3 |
| accessibility_first_user | Representation 2.1, Action 3.1 |
| middle_school_explorer | Engagement 1.2, Action 3.3 |
| artist / writer / musician | Action 3.2 |
| low_bandwidth_offline_user | Representation 2.1 (cached), robust offline |

Full persona list: `product/PERSONA_MATRIX.md`.

---

## 7. Gaps for UDL evidence

| Gap | Next step |
|-----|-----------|
| No classroom pilot data | Partner school observation protocol |
| Placeholder apps limit expression | Ship one real tool per creator mode |
| No reading-level automated check | Add copy lint for simplified_language strings |
| Switch/voice not implemented | AT partner review when implemented |

---

## 8. Related documents

- [ACCESSIBILITY_AND_INCLUSION.md](ACCESSIBILITY_AND_INCLUSION.md)
- [PREK_TO_POSTDOC_USE_CASES.md](PREK_TO_POSTDOC_USE_CASES.md)
- [SCOOTER_TO_SPACESHIP_MODEL.md](SCOOTER_TO_SPACESHIP_MODEL.md)
- `product/ACCESSIBILITY_REQUIREMENTS.md` §4
