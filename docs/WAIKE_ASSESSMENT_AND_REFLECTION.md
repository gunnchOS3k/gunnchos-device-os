# WAIKE Assessment and Reflection

**Status:** device OS alpha · rubric templates for tutor cards and student tasks  
**Config inputs:** `waike_tutor_cards.yaml`, `waike_student_tasks.yaml`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Assessment philosophy

WAIKE assessment in gunnchos-device-os emphasizes:

1. **Understanding boundaries** — alpha vs shipping OS; mock vs real telemetry
2. **Privacy ethics** — especially for School, Guardian, Laboratory pathways
3. **Artifact quality** — submitted files from student tasks
4. **Reflection** — every tutor card includes `reflection_question`

Not standardized testing or certified competencies.

---

## Rubric dimensions (1–4 scale)

| Dimension | 1 — Emerging | 2 — Developing | 3 — Proficient | 4 — Exemplary |
|-----------|--------------|----------------|----------------|---------------|
| Claim accuracy | Confuses alpha with shipping OS | Mostly accurate with gaps | Uses claim boundary language | Teaches others correct boundaries |
| Privacy awareness | Shares sensitive data in artifact | Minimal leaks | Follows safety_privacy_note | Identifies unstated risks |
| Task completion | Missing output | Partial output | Complete output_artifact | Extends beyond prompt |
| Reflection depth | One word / absent | Single sentence | Answers reflection_question | Connects to community context |
| Technical execution | Demo won't run | Runs with help | pytest or demo passes locally | Improves test or doc |

---

## Task-specific expectations

| Task ID | Pass criteria | Stretch |
|---------|---------------|---------|
| prek_safe_task | Describes tap interaction | Names colors without PII |
| middle_school_task | Submits diagram file | Explains circuit in words |
| high_school_task | essay_draft.md ≥ 100 words | Citation placeholder used correctly |
| college_task | test_results.txt from local run | Opens docs PR |
| research_measurement_task | JSON export with consent narrative | Links to Edge-IO contract doc |
| community_library_task | Completes lesson without login | Explains anonymous token purpose |

---

## Tutor card reflection prompts

Each card's `reflection_question` is the primary formative assessment:

| Card | Reflection focus |
|------|------------------|
| scooter_letters | Generalization (find A in environment) |
| school_wireless_basics | Offline/online contrast |
| studio_story_seed | Sensory writing preference |
| workshop_first_script | Next program goal |
| lab_field_measurement | Data that must stay on device |
| guardian_screen_balance | Time away from screen |
| offline_reading_pack | Sync behavior when online |
| gunnchai_reflection | Teaching a friend |

---

## Portfolio integration (waike-research-ops)

Recommended portfolio bundle:

1. Output artifact from student task
2. 3–5 sentence reflection answer
3. Screenshot of launcher mock OR pytest log (redacted)
4. Explicit **claim boundary** sentence in cover note

Template: `waike-research-ops/templates/project_story_card.md`

---

## Formative vs summative

| Type | Use in alpha |
|------|--------------|
| Formative | reflection_question in class discussion |
| Summative | rubric on portfolio bundle for course grade |
| Standardized | **Not supported** — no psychometric validation |

---

## Academic integrity

- Students may collaborate on pytest/setup
- Individual reflection must be own words
- Do not submit synthetic fleet telemetry as real field data
- Label all `results/*.json` as demo output

---

## Instructor checklist

- [ ] Stated alpha disclaimer at session start
- [ ] Selected mode appropriate for audience
- [ ] safety_privacy_note read aloud for youth/research cards
- [ ] Collected output + reflection
- [ ] Scored with rubric (if graded)
- [ ] No secrets in submitted artifacts

---

## Claim boundary

Rubrics assess **learning about prototype OS governance** — not WCAG certification or COPPA compliance proof.

---

## Related documents

- [WAIKE_TUTOR_CARDS.md](WAIKE_TUTOR_CARDS.md)
- [WAIKE_STUDENT_TASKS.md](WAIKE_STUDENT_TASKS.md)
- [WAIKE_INSTRUCTOR_GUIDE.md](WAIKE_INSTRUCTOR_GUIDE.md)
