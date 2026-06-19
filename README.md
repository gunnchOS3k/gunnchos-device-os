# gunnchos Device OS

Operating system / software layer for **gunnchOS** modular consoles (research scaffold).

> Not a shipping OS image. Launcher mock demonstrates UX contracts.

## Modes

School, Developer, Play, Research Measurement — plus parental controls and privacy-preserving telemetry stubs.

## Integrations

- [edge-io-measurement-node](https://github.com/gunnchOS3k/edge-io-measurement-node)
- [7gc-digital-twin](https://github.com/gunnchOS3k/7gc-digital-twin)
- [waike-research-ops](https://github.com/gunnchOS3k/waike-research-ops)

```bash
pip install -r requirements.txt && pytest -q
cd apps/launcher_mock && npm install && npm run dev
```

---

## What is this?

**Software layer for school, research, play, and measurement modes on gunnchos devices—integrating WAIKE, AI tutors, and 7GC exports.**

| | |
|---|---|
| **Status** | Device OS prototype repo |
| **Evidence today** | Level 1 smoke test — see [Evidence status](#evidence-status-smoke-test-vs-real-validation) |
| **Start** | [docs/START_HERE.md](docs/START_HERE.md) |

## What problem does this solve?

**Human:** Shared school devices need safe modes, consent, and research hooks without surveillance.

**Technical:** Installable shell, mode manager, telemetry bridge, fleet POC, update architecture.

**Who is harmed if unsolved:** Students and admins if modes leak data or lack governance.

**Gary / 7GC / digital equality:** This repo supports equitable connectivity research for under-connected communities; Gary is the flagship urban anchor where applicable.

## Beginner mental model

The **dashboard and rulebook** telling each device how to behave in class, lab, or field.

## How this repo addresses the problem

Python launcher modules, launcher mock UI, tests, bridge contracts to Edge-IO/7GC.

**Main output:** Mock UI + module tests (`make e2e` smoke)—not a shipping OS image.

**Output does NOT prove:** Production MDM or secure boot on hardware.

## How this fits gunnchOS3k MLV

Software face of hardware + Edge-IO + WAIKE + gunnchAI3k.

Deep dive: [docs/HOW_THIS_FITS_GUNNCHOS.md](docs/HOW_THIS_FITS_GUNNCHOS.md) · [docs/CROSS_REPO_DEPENDENCY_MAP.md](docs/CROSS_REPO_DEPENDENCY_MAP.md) (where present)

## How this fits 6G PhD research

Relevant themes: **Edge AI · trust/privacy · testbed UX · education fleet management**

Oulu/CWC-style alignment (research direction, not affiliation claim): [docs/HOW_THIS_FITS_6G_PHD_RESEARCH.md](docs/HOW_THIS_FITS_6G_PHD_RESEARCH.md)

## What exists today

- gunnchos_launcher package
- launcher_mock app
- Tests
- Bridge stubs

Details: [docs/WHAT_IS_REAL_TODAY.md](docs/WHAT_IS_REAL_TODAY.md)

## Evidence status: smoke test vs real validation

- `make smoke` / `make e2e` = **CI smoke test** — proves code runs, **not** that research claims are field-validated.
- See [docs/NO_MORE_TOY_DEMOS.md](docs/NO_MORE_TOY_DEMOS.md) · [docs/EVIDENCE_STANDARD.md](docs/EVIDENCE_STANDARD.md) · [quality/CLAIMS_TO_EVIDENCE_MATRIX.md](quality/CLAIMS_TO_EVIDENCE_MATRIX.md)

**Next real evidence needed:**

- Installable app
- Real telemetry
- Fleet POC
- Secure update model

## Run or inspect this repo

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make e2e
```

| | |
|---|---|
| **Output** | `test + smoke artifacts` |
| **Means** | Reproducible smoke artifacts for CI and reviewers |
| **Does not mean** | Conference, adoption, or manufacturing readiness |

Video: [docs/video_walkthrough_script.md](docs/video_walkthrough_script.md)

## Visual map

```mermaid
flowchart LR
  DeviceOS[gunnchos-device-os] --> EdgeIO[edge-io]
  WAIKE --> DeviceOS
  gunnchAI --> DeviceOS
```

More diagrams: [docs/diagrams/README.md](docs/diagrams/README.md) (if present) · [docs/uml/README.md](docs/uml/README.md) (spectrumx)

## Start here based on who you are

| Reader | Start here | You will learn |
|--------|------------|----------------|
| Beginner | [docs/PLAIN_ENGLISH_EXPLANATION.md](docs/PLAIN_ENGLISH_EXPLANATION.md) | Idea without jargon |
| Student / WAIKE | [docs/AUDIENCE_GUIDE.md](docs/AUDIENCE_GUIDE.md) | Learning path |
| Researcher / professor | [docs/HOW_THIS_FITS_6G_PHD_RESEARCH.md](docs/HOW_THIS_FITS_6G_PHD_RESEARCH.md) | Research fit |
| Contributor | [CONTRIBUTING.md](CONTRIBUTING.md) or Issues | How to help |
| City / school partner | [docs/PROBLEM_SOLUTION_MAP.md](docs/PROBLEM_SOLUTION_MAP.md) | Why it matters locally |

## What would make this final?

**Not satisfied yet** for final / conference / adoption / manufacturing gates—see audit:

- [docs/WHAT_WOULD_MAKE_THIS_FINAL.md](docs/WHAT_WOULD_MAKE_THIS_FINAL.md)
- [quality/FINAL_READINESS_CONFIRMATION.md](quality/FINAL_READINESS_CONFIRMATION.md)

## Roadmap from current state to final readiness

| Gate | Status |
|------|--------|
| Concept | Met |
| Smoke test | Met (`make smoke`) |
| Real evidence pipeline | Open |
| Benchmark / field data | Open |
| Internal validation | Open |
| External reproduction | Open |
| Candidate release | Open |
| Final | Not claimed |

Full table: [quality/READINESS_GATE_TABLE.md](quality/READINESS_GATE_TABLE.md)

## Related repos in the 7GC research spine


| Repo | Role |
|------|------|
| [7gc-digital-twin](https://github.com/gunnchOS3k/7gc-digital-twin) | Community digital twin spine |
| [spectrumx-ai-ran-gary](https://github.com/gunnchOS3k/spectrumx-ai-ran-gary) | AI-RAN + SpectrumX competition path |
| [readygary-6g-beam-selection](https://github.com/gunnchOS3k/readygary-6g-beam-selection) | Beam selection / PHY-facing evidence |
| [edge-io-measurement-node](https://github.com/gunnchOS3k/edge-io-measurement-node) | Privacy-first edge measurement |
| [ntn-resilience-sim](https://github.com/gunnchOS3k/ntn-resilience-sim) | NTN + terrestrial resilience |
| [waike-research-ops](https://github.com/gunnchOS3k/waike-research-ops) | Education & workforce pipeline |
| [gunnchos-hardware-industrial-design](https://github.com/gunnchOS3k/gunnchos-hardware-industrial-design) | Device hardware EVT planning |
| [gunnchos-device-os](https://github.com/gunnchOS3k/gunnchos-device-os) | School/research device OS prototype |
| [gunnchAI3k](https://github.com/gunnchOS3k/gunnchAI3k) | Learning assistant (where relevant) |


## Claims and non-claims

**Supports today:** Runnable scaffold, documented methods, smoke-test artifacts, honest limitations.

**Does not prove yet:** Production MDM or secure boot on hardware.

**Requires evidence issues:** See GitHub `[Evidence TODO]` issues and `quality/CLAIMS_TO_EVIDENCE_MATRIX.md`.

---

## Industry / research-grade tooling alignment

| Tool / ecosystem | Why it matters | Adapter | Runs now? | Access? |
|------------------|----------------|---------|-----------|---------|
| See matrix | Evidence upgrade path | `industry_research_stack/` | Stub exports | Optional |

**Commands:** `make e2e` (includes tool export stubs) · `python3 scripts/run_all_tool_exports.py`

**Notice:** Aligned with public research ecosystems — [non-affiliation](industry_research_stack/NON_AFFILIATION_NOTICE.md). Smoke stubs only unless documented otherwise.

## Wireless engineering alignment

See [docs/WIRELESS_ENGINEERING_ALIGNMENT.md](docs/WIRELESS_ENGINEERING_ALIGNMENT.md).


---

## EVT-1 OS alpha (this pass)

**Status:** EVT-1 alpha prototype — **not** a shipping OS.

```bash
pip install -r requirements.txt
PYTHONPATH=. pytest -q tests/test_mode_manager.py tests/test_policy_engine.py tests/test_device_profiles.py
python3 scripts/run_device_os_demo.py
```

Demo output: [results/device_os_evt1_demo_output.json](results/device_os_evt1_demo_output.json)

| Real today | Mock / prototype | Not claimed |
|------------|------------------|-------------|
| Full PRD-aligned `gunnchos_device_os` (21 modules) | Steam/WSL detect, update server, secure boot | Finished OS, certified secure boot, production MDM |
| 7 modes incl. Coder · 8 profiles | Media DRM routes · device health metrics | Shipping console OS |
| Mode/profile/policy tests + demo JSON | Installable signed image | Steam/media licensing |

Hardware contract: [docs/HARDWARE_SOFTWARE_CONTRACT.md](docs/HARDWARE_SOFTWARE_CONTRACT.md)
