# WAIKE Tutor Cards

**Status:** device OS alpha · instructor prompt catalog  
**Config:** `config/waike_tutor_cards.yaml`  
**Module:** referenced by WAIKE demos and School/Guardian/Lab modes

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Card schema

Each card in `tutor_cards` includes:

| Field | Purpose |
|-------|---------|
| card_id | Stable identifier |
| audience | pre_k, high_school, writer, cs_student, researcher, parent, library, middle_school |
| mode | gunnchOS mode context |
| learning_goal | Instructor objective |
| prompt | Opening tutor line |
| student_task | Actionable assignment |
| reflection_question | Metacognition follow-up |
| safety_privacy_note | Boundaries for youth/research |
| offline_option | true/false |
| output_artifact | Expected deliverable filename |

Validated by `tests/test_waike_integration.py` (≥6 cards, required fields).

---

## Card catalog

| card_id | Audience | Mode | Learning goal | Offline |
|---------|----------|------|---------------|---------|
| scooter_letters | pre_k | Scooter | Letter recognition | ✓ |
| school_wireless_basics | high_school | School | Wireless basics | ✓ |
| studio_story_seed | writer | Studio | Creative writing warm-up | ✓ |
| workshop_first_script | cs_student | Workshop | First Python program | ✓ |
| lab_field_measurement | researcher | Laboratory | Ethical field measurement | ✗ |
| guardian_screen_balance | parent | Guardian | Healthy screen balance | ✓ |
| offline_reading_pack | library | Offline | Offline reading continuity | ✓ |
| gunnchai_reflection | middle_school | School | Metacognition via tutor | ✓ |

---

## Sample card — school_wireless_basics

```yaml
prompt: "What happens when your device connects to Wi-Fi?"
student_task: Draw a simple home network with phone, router, and internet cloud.
reflection_question: "What would change if the internet went offline?"
safety_privacy_note: Do not share passwords or personal network details.
output_artifact: network_sketch.md
```

---

## Sample card — lab_field_measurement

```yaml
student_task: Start a mock measurement session and export CSV metadata only.
safety_privacy_note: No private packet capture. Location off by default.
output_artifact: measurement_export.csv
```

Links to [EDGE_IO_INTEGRATION_CONTRACT.md](EDGE_IO_INTEGRATION_CONTRACT.md).

---

## Sample card — guardian_screen_balance

```yaml
safety_privacy_note: Guardian controls are a stub — not production enforcement.
output_artifact: screen_balance_checklist.md
```

Honest claim boundary for issue #7.

---

## Instructor usage

1. Pick card matching class mode (School, Workshop, Laboratory, …)
2. Read prompt aloud or via gunnchAI3k `/mentor` (cross-repo)
3. Assign student_task during device lab
4. Close with reflection_question
5. Collect output_artifact — no secrets in submissions

See [WAIKE_INSTRUCTOR_GUIDE.md](WAIKE_INSTRUCTOR_GUIDE.md).

---

## Adding cards

1. Edit `config/waike_tutor_cards.yaml`
2. Run `pytest tests/test_waike_integration.py`
3. Document in this file
4. PR with `Closes #12` if backlog-driven

---

## Claim boundary

Tutor cards are **instructor content stubs** — not psychometrically validated assessments.
