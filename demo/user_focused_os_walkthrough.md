# User-Focused OS Walkthrough

**Audience:** Reviewers, partners, contributors  
**Duration:** ~20 minutes  
**Status:** synthetic demo — not deployment proof  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Prerequisites

```bash
cd gunnchos-device-os
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python3 scripts/validate_user_focused_os.py
PYTHONPATH=. python3 scripts/run_user_focused_os_demo.py
```

Optional launcher mock:

```bash
cd apps/launcher_mock && npm install && npm run dev
```

---

## Walkthrough narrative

### 1. What this layer is (2 min)

Explain: gunnchOS user-focused layer is a **profile-driven shell** above hardware. It answers who is using the device and how complex the interface should be — from Scooter (pre-K) to Spaceship (postdoc).

Point to: `docs/USER_FOCUSED_OS_ARCHITECTURE.md`

### 2. Run the demo (3 min)

```bash
PYTHONPATH=. python3 scripts/run_user_focused_os_demo.py | head -80
```

Open `results/user_focused_os_demo_output.json`. Note:

- `claim_boundary` string
- `scenario_count` (11 scenarios)
- Each scenario: profile, journey_preset, workspace, recommendations

**Say explicitly:** "This JSON is synthetic demo output, not field telemetry."

### 3. Onboarding (3 min)

Show `onboarding_sample` in demo output or run:

```python
from gunnchos_device_os.onboarding_wizard import run_onboarding
run_onboarding({
    "who": "student", "goal": "learn", "control": "guided",
    "accessibility_needs": [], "offline": False, "guardian": False,
    "display_name": "Demo Student", "user_id": "walkthrough-1",
})
```

Seven questions map to persona, preset, app pack, workspace, guardian, offline, a11y.

### 4. Persona → preset → pack chain (4 min)

Pick **high school student**:

- Persona: `high_school_student` in `config/personas.yaml`
- Preset: `car`
- Pack: `learn_pack` + apps like vscode, browser
- Workspace: `homework_desk`

Pick **writer**:

- Preset: `studio`, pack: `write_pack`, workspace: `essay_studio`
- Creator workflow in demo scenario `writer_studio`

### 5. Policy and safety (3 min)

Contrast:

- `pre_k_learner` blocked_apps: steam, browser, youtube
- `gamer` preset: arcade, steam allowed (with guardian windows)

Show guardian scenario in demo JSON — `"mock": true`.

### 6. Accessibility overlay (2 min)

Scenario `accessibility_first`: high_contrast theme, large_text, reduced_motion applied via `CustomizationEngine` + `accessibility_manager`.

### 7. Honest limits (3 min)

Close with `docs/USER_FOCUSED_OS_LIMITATIONS.md`:

- Not a shipping OS
- Placeholder creative apps
- No user-tested UX claim yet

---

## Checklist for presenters

- [ ] Said "alpha" and "not shipping OS" in first 60 seconds
- [ ] Labeled demo JSON as synthetic
- [ ] Mentioned guardian mock, not production MDM
- [ ] Did not claim WCAG certification or user-tested UX
- [ ] Pointed to CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md for evidence boundaries

---

## Related walkthroughs

- [scooter_to_spaceship_walkthrough.md](scooter_to_spaceship_walkthrough.md)
- [persona_demo_transcripts.md](persona_demo_transcripts.md)
- [accessibility_walkthrough.md](accessibility_walkthrough.md)
- [creator_workflow_walkthrough.md](creator_workflow_walkthrough.md)
- [offline_first_walkthrough.md](offline_first_walkthrough.md)
- [device_os_evt1_walkthrough.md](device_os_evt1_walkthrough.md) — EVT modes parallel path
