# Creator Workstation Test Plan

**Version:** 1.0

---

## Purpose

Validate writer, artist, and music workspace routes, templates, export, and creator accessibility settings.

---

## Setup

- Personas: Writer, Musician, Artist from user-focused demo
- Launcher mock creator tabs or OS-layer build
- Offline creator template pack (when available)

---

## Personas covered

- Writer (Studio)
- Musician (Music Studio)
- Artist (Art Table)
- Accessibility-first user in creator context

---

## Device classes covered

- Student 14.5 (primary)
- Handheld Hybrid (simplified creator)
- DS-XL Coder (hybrid code+media)

---

## Test steps

| ID | Step |
|----|------|
| C-01 | Open writer workspace — primary action visible |
| C-02 | Save document locally |
| C-03 | Export MD/DOCX/PDF (mock or real app) |
| C-04 | Open artist workspace — stylus path if available |
| C-05 | Open music workspace |
| C-06 | Offline project open/save |
| C-07 | High contrast in creator chrome |
| C-08 | Destructive delete — confirm + undo window |

---

## Expected results

- One primary action per creator screen
- Local save works offline
- Export produces file artifact
- A11y settings persist in creator apps

---

## Evidence to collect

- Export file hashes
- Screenshots per workspace
- UAT sub-scenarios in master report

---

## Pass/fail criteria

**Pass:** C-01–C-08 pass for mock or integrated apps; 0 P0 data loss.

**Fail:** Dead-end screen; export silently fails; no confirm on delete.

---

## Known limitations

- Video/streaming placeholder not tested
- Real creative suite integration future work
- Handheld full DAW may be out of scope
