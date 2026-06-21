# WAIKE Student Tasks

**Status:** device OS alpha · audience-scoped assignments  
**Config:** `config/waike_student_tasks.yaml`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Task schema

Each entry under `student_tasks`:

| Field | Purpose |
|-------|---------|
| audience | Target learner profile |
| mode | gunnchOS mode for task context |
| task | Assignment description |
| output | Expected artifact name |
| offline | Whether task works offline |

---

## Task catalog

| Task ID | Audience | Mode | Output | Offline |
|---------|----------|------|--------|---------|
| prek_safe_task | pre_k | Scooter | color_match_score | ✓ |
| elementary_task | elementary | Bicycle | reading_progress | ✓ |
| middle_school_task | middle_school | School | circuit_diagram.png | ✓ |
| high_school_task | high_school | Car | essay_draft.md | ✓ |
| college_task | college | Workshop | test_results.txt | ✓ |
| creator_task | artist | Studio | mood_board.canvas | ✓ |
| game_dev_task | game_developer | Workshop | level_prototype.json | ✓ |
| hardware_maker_task | hardware_engineer | Workshop | wiring_plan.md | ✓ |
| research_measurement_task | researcher | Laboratory | measurement_export.json | ✗ |
| community_library_task | library | Library | anonymous_progress_token | ✓ |

---

## Mode pathways

From `mode_pathways` in same config file:

| Mode | Pathway ID |
|------|------------|
| Scooter | beginner_learning |
| School | structured_lessons |
| Studio | creative_projects |
| Workshop | coding_game_jam |
| Laboratory | research_measurement |
| Guardian | youth_safety |
| Offline | low_bandwidth_access |

See [WAIKE_DEVICE_PATHWAYS.md](WAIKE_DEVICE_PATHWAYS.md).

---

## Offline lessons API

```python
from gunnchos_device_os.waike_integration import list_offline_lessons, deploy_lesson

list_offline_lessons()
deploy_lesson("wireless_basics_101", "high_school")
```

Offline packs: `waike_gary_upnow_intro`, `wireless_basics_101`, `python_starter_pack`.

---

## Journey preset alignment

| Task mode | Journey preset examples |
|-----------|------------------------|
| Scooter / Bicycle | Pre-K / elementary journeys |
| Car | High school essay workflow |
| Workshop | CS / maker jams |
| Laboratory | Spaceship / research preset on ds_xl_coder |

Cross-link: [SCOOTER_TO_SPACESHIP_MODEL.md](SCOOTER_TO_SPACESHIP_MODEL.md).

---

## Assessment

Tasks define **output artifacts** — grading rubrics in [WAIKE_ASSESSMENT_AND_REFLECTION.md](WAIKE_ASSESSMENT_AND_REFLECTION.md).

---

## Tests

```bash
PYTHONPATH=. pytest tests/test_waike_integration.py::test_student_tasks
```

---

## Claim boundary

Tasks are **design templates** — not deployed LMS assignments with auto-grading.
