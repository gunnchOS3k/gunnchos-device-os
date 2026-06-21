# WAIKE Device OS Walkthrough

**Status:** device OS alpha · end-to-end WAIKE demo on gunnchos-device-os

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Goals

After this walkthrough you will:

1. List WAIKE tutor cards and student tasks from YAML
2. Deploy a mock offline lesson
3. Connect a tutor card to a gunnchOS mode
4. Run integration demo JSON output
5. Optional: explore launcher mock user-focused pathways

---

## Step 1 — Setup

```bash
cd gunnchos-device-os
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## Step 2 — Run WAIKE integration demo

```bash
python scripts/run_waike_integration_demo.py
```

Open `results/waike_integration_demo_output.json`:

- `tutor_cards` — 8 card IDs
- `sample_card` — school_wireless_basics
- `student_tasks` — 10 task IDs
- `mode_pathways` — mode → pathway map
- `offline_lessons` — three lesson pack IDs
- `deploy` — mock lesson deploy result
- `claim_boundary` — alpha disclaimer

---

## Step 3 — Explore tutor cards

```bash
PYTHONPATH=. python -c "
import yaml
from pathlib import Path
cards = yaml.safe_load(Path('config/waike_tutor_cards.yaml').read_text())['tutor_cards']
for cid, c in cards.items():
    print(c['mode'], c['audience'], c['learning_goal'])
"
```

Pick one card for classroom use — see [docs/WAIKE_TUTOR_CARDS.md](../docs/WAIKE_TUTOR_CARDS.md).

---

## Step 4 — Student task + pathway

```python
import yaml
from pathlib import Path
data = yaml.safe_load(Path("config/waike_student_tasks.yaml").read_text())
task = data["student_tasks"]["middle_school_task"]
print(task["task"], "→", task["output"])
print("Pathway:", data["mode_pathways"][task["mode"]])
```

---

## Step 5 — Offline lesson deploy

```python
from gunnchos_device_os.waike_integration import list_offline_lessons, deploy_lesson

print(list_offline_lessons())
r = deploy_lesson("python_starter_pack", "cs_student")
assert r["deployed"] and r["mock"]
```

---

## Step 6 — Cross-link Edge-IO (research track)

For `research_measurement_task`:

```python
from gunnchos_device_os.edge_io_contract import start_field_session
r = start_field_session("instructor", "ds_xl_coder", consent=True, research_operator=True)
assert r["started"]
```

Follow [demo/edge_io_integration_walkthrough.md](edge_io_integration_walkthrough.md).

---

## Step 7 — Launcher mock (optional)

```bash
cd apps/launcher_mock && npm install && npm run dev
```

1. Open user-focused view
2. Select **high_school_student** persona
3. Choose **Car** or **School** journey
4. Review **Home** tab summary

---

## Step 8 — Tests

```bash
PYTHONPATH=. pytest tests/test_waike_integration.py -v
```

---

## Reflection (WAIKE)

Answer for portfolio:

1. What is the difference between a gunnchOS **mode** and a WAIKE **pathway**?
2. Which tutor card safety note matters most for your community?
3. Why does `deploy_lesson()` return `mock: true`?

---

## Instructor pointer

Full session plans: [docs/WAIKE_INSTRUCTOR_GUIDE.md](../docs/WAIKE_INSTRUCTOR_GUIDE.md)

Assessment rubric: [docs/WAIKE_ASSESSMENT_AND_REFLECTION.md](../docs/WAIKE_ASSESSMENT_AND_REFLECTION.md)

---

## Claim boundary

Demo JSON and mock deploys are **synthetic** — not proof of classroom deployment or LMS integration.
