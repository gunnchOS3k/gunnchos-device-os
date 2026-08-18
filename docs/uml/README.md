# UML — gunnchos-device-os

Authoritative architecture for **this repository**: Paper I *infrastructure* for
**Resilience-Aware Service Continuity in Heterogeneous 6G Networks**.

This is a research prototype (launcher mock, Python policy/runtime, digital image
path). It is **not** a shipping OS and **not** physical-boot evidence.

| Lane | Meaning |
|---|---|
| **current/** | Modules, configs, and Make targets that exist in this checkout |
| **future/** | Physical EVT boot, signed OTA, carrier attach — still `PHYSICAL_PENDING` |
| **legacy/** | One-line placeholder `docs/uml/README.md` that this pack replaces |

**Render.** GitHub renders Mermaid in the Markdown pages. Optional PlantUML:

```bash
./docs/uml/render_plantuml.sh
# or: make uml
```

**Traceability:** [traceability_matrix.md](traceability_matrix.md)

- [Current index](current/index.md)
- [Future index](future/index.md)
- [Legacy index](legacy/index.md)
