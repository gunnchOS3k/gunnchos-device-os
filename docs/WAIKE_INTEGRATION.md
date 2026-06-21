# WAIKE Integration — gunnchos-device-os

**Status:** device OS alpha · config-driven education pathways  
**Module:** `gunnchos_device_os/waike_integration.py`  
**Config:** `config/waike_tutor_cards.yaml`, `config/waike_student_tasks.yaml`  
**External:** [waike-research-ops](https://github.com/gunnchOS3k/waike-research-ops), [gunnchAI3k](https://github.com/gunnchOS3k/gunnchAI3k)

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## What WAIKE is in this repo

**WAIKE** (Wireless + Artificial Intelligence Kinesthetic Education) integration in gunnchos-device-os connects:

- **Device OS modes** (School, Studio, Workshop, Laboratory, Guardian, Offline, …)
- **Tutor cards** — instructor prompts with safety/privacy notes
- **Student tasks** — audience-scoped assignments with output artifacts
- **Offline lesson packs** — mock deploy via `waike_integration.py`
- **gunnchAI3k tutor** — referenced in modes and tutor cards (cross-repo)

This is an **alpha integration layer** — not a full LMS or certified curriculum platform.

---

## Python API

```python
from gunnchos_device_os.waike_integration import list_offline_lessons, deploy_lesson

list_offline_lessons()
# ['waike_gary_upnow_intro', 'wireless_basics_101', 'python_starter_pack']

deploy_lesson("python_starter_pack", "student")
# deployed: True, offline_capable: True, mock: True
```

---

## Configuration files

| File | Contents |
|------|----------|
| `config/waike_tutor_cards.yaml` | 8 tutor cards (pre-K through researcher/parent) |
| `config/waike_student_tasks.yaml` | 10 student tasks + mode_pathways map |

---

## Documentation map

| Doc | Purpose |
|-----|---------|
| [WAIKE_TUTOR_CARDS.md](WAIKE_TUTOR_CARDS.md) | Card catalog |
| [WAIKE_STUDENT_TASKS.md](WAIKE_STUDENT_TASKS.md) | Task ladder |
| [WAIKE_DEVICE_PATHWAYS.md](WAIKE_DEVICE_PATHWAYS.md) | Mode → pathway mapping |
| [WAIKE_INSTRUCTOR_GUIDE.md](WAIKE_INSTRUCTOR_GUIDE.md) | Teaching with this repo |
| [WAIKE_ASSESSMENT_AND_REFLECTION.md](WAIKE_ASSESSMENT_AND_REFLECTION.md) | Rubrics and reflection |
| [demo/waike_device_os_walkthrough.md](../demo/waike_device_os_walkthrough.md) | Hands-on demo |

Legacy: [WAIKE_SCHOOL_MODE.md](WAIKE_SCHOOL_MODE.md), [docs/09_GUNNCHAI3K_AND_WAIKE_INTEGRATION.md](09_GUNNCHAI3K_AND_WAIKE_INTEGRATION.md)

---

## What WAIKE teaches from this repo

- Device OS modes and privacy boundaries for school/research devices
- DS-XL deploy workflow (alpha mock) for classroom project sharing
- Edge-IO ethical measurement (consent-first)
- Scooter-to-spaceship UX via launcher mock user-focused view
- Guardian and offline modes for youth and low-bandwidth contexts

---

## Audience pathways

| Audience | Entry mode | Sample artifact |
|----------|------------|-----------------|
| Pre-K | Scooter / Bicycle | color_match_score |
| K-12 | School | essay_draft.md, circuit_diagram.png |
| CS student | Workshop | test_results.txt, hello.py |
| Researcher | Laboratory | measurement_export.json |
| Parent | Guardian | screen_balance_checklist.md |
| Library patron | Library / Offline | anonymous_progress_token |

---

## gunnchAI3k tutor integration

Modes allow `gunnchai3k` and `waike_offline` apps (placeholders). Tutor card `gunnchai_reflection` demonstrates metacognition prompts with privacy-safe wording.

Skill tree cross-link: `waike-research-ops/knowledge_maps/waike_skill_tree.yaml` → repo `gunnchos-device-os`.

Discord `/mentor` and `/portfolio` flows live in waike-research-ops — not implemented in device-os alpha.

---

## Demo and tests

```bash
python scripts/run_waike_integration_demo.py
# → results/waike_integration_demo_output.json

PYTHONPATH=. pytest tests/test_waike_integration.py
```

---

## Portfolio artifacts (students)

- Lab report without secrets
- Demo screenshot of launcher mock user-focused flow
- JSON output from integration demo
- Story card from waike-research-ops templates

---

## Task ladder

| Level | Task |
|-------|------|
| Beginner | Clone repo, run pytest, summarize README in plain English |
| Intermediate | Pass CI locally; extend WAIKE tutor card YAML; docs PR |
| Advanced | Capstone integrating Edge-IO + deploy contract; research notebook |

Issues: label `good-first-research-task` where applicable.

---

## Claim boundary

| Allowed | Forbidden |
|---------|-----------|
| "WAIKE tutor cards defined in YAML" | "Certified curriculum" |
| "Offline lesson list mock" | "Full waike-research-ops sync" |
| "Device pathways map modes to learning tracks" | "User-tested classroom outcomes" |

See `product/CLAIM_BOUNDARY.md`.

---

## Related repos

| Repo | Role |
|------|------|
| waike-research-ops | Workforce pipeline, skill tree, portfolio templates |
| gunnchAI3k | Tutor / mentor Discord bot |
| edge-io-measurement-node | Field measurement for Laboratory pathway |
| 7gc-digital-twin | Community research exports |
