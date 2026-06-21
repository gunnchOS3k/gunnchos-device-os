# WAIKE Instructor Guide

**Status:** device OS alpha · teaching with gunnchos-device-os  
**Audience:** K-12 teachers, university instructors, WAIKE mentors

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Before class

1. Read [product/CLAIM_BOUNDARY.md](../product/CLAIM_BOUNDARY.md) — use **device OS alpha** language with students
2. Install repo: `pip install -r requirements.txt && pytest -q`
3. Optional: run launcher mock for UX demo
4. Pick tutor card from [WAIKE_TUTOR_CARDS.md](WAIKE_TUTOR_CARDS.md)
5. Match student task from [WAIKE_STUDENT_TASKS.md](WAIKE_STUDENT_TASKS.md)

---

## Session plans by duration

### 30-minute intro (Beginner)

| Min | Activity |
|-----|----------|
| 0–5 | Plain English: what is gunnchOS device OS alpha? |
| 5–10 | Run `pytest -q tests/test_device_classes.py` — four device classes |
| 10–20 | Launcher mock user-focused: pick persona |
| 20–30 | Reflection: scooter vs spaceship metaphor |

### 60-minute school lab (Intermediate)

| Min | Activity |
|-----|----------|
| 0–10 | School mode policy — what's blocked and why |
| 10–25 | Tutor card `school_wireless_basics` — network sketch |
| 25–40 | Guardian policy demo — why steam needs approval |
| 40–50 | Privacy: child telemetry off |
| 50–60 | Portfolio: screenshot + 3-sentence summary |

### 90-minute research lab (Advanced)

| Min | Activity |
|-----|----------|
| 0–15 | Research Measurement mode + consent ethics |
| 15–45 | Edge-IO walkthrough ([demo/edge_io_integration_walkthrough.md](../demo/edge_io_integration_walkthrough.md)) |
| 45–70 | Tutor card `lab_field_measurement` |
| 70–90 | Export discussion — what must never leave device |

---

## Mode selection guide

| Teaching goal | Mode | Tutor card / task |
|---------------|------|-------------------|
| Letters / pre-K | Scooter preset | scooter_letters |
| Essay writing | School / Car | high_school_task |
| First code | Workshop | workshop_first_script |
| Creative writing | Studio | studio_story_seed |
| Screen time discussion | Guardian | guardian_screen_balance |
| Library / shared PC | Offline / Library | offline_reading_pack, community_library_task |
| Field research ethics | Laboratory | lab_field_measurement, research_measurement_task |

---

## gunnchAI3k mentor mode

For Discord-enabled classes:

- Use `/mentor` with topics from waike-research-ops skill tree
- Assign `/portfolio` summary after local pytest success
- **Do not** paste secrets, passwords, or private network details into tutor (aligned with tutor card safety notes)

---

## DS-XL deploy demo (optional)

For CS classrooms with developer audience:

```bash
python scripts/run_deploy_contract_demo.py
```

Discuss consent and guardian gates — [demo/ds_xl_deploy_walkthrough.md](../demo/ds_xl_deploy_walkthrough.md).

---

## Assessment

Use [WAIKE_ASSESSMENT_AND_REFLECTION.md](WAIKE_ASSESSMENT_AND_REFLECTION.md) for rubrics. Focus on process and privacy awareness, not production OS mastery.

---

## Safety talking points

1. Guardian controls are **mock** — discuss real family/school policies separately
2. No private packet capture in research mode design
3. Shared devices: use Library/Offline tasks without personal account sign-in
4. Synthetic telemetry in fleet mock is labeled — not real student data

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| pytest fails | `pip install pytest pyyaml` |
| launcher mock won't start | `cd apps/launcher_mock && npm install` |
| WAIKE demo import error | `PYTHONPATH=.` from repo root |

---

## Claim boundary for instructors

Tell students:

> We are using a research prototype that shows how a device OS *could* behave. It is not the operating system on a store-bought laptop yet.

---

## Related documents

- [WAIKE_INTEGRATION.md](WAIKE_INTEGRATION.md)
- [AUDIENCE_GUIDE.md](AUDIENCE_GUIDE.md)
- [PREK_TO_POSTDOC_USE_CASES.md](PREK_TO_POSTDOC_USE_CASES.md)
