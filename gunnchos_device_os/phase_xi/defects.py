from __future__ import annotations
import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any


SEVERITIES = ("U0", "U1", "U2", "U3", "U4")


@dataclass
class Defect:
    id: str
    journey: str
    step: str
    severity: str
    root_cause: str
    repo: str
    component: str
    fix: str
    regression: str
    status: str  # OPEN | FIXED | BLOCKED_PHYSICAL | BLOCKED_EXTERNAL
    classification: str = "DIGITAL"  # DIGITAL | PHYSICAL | EXTERNAL

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DefectRegister:
    root: Path
    defects: list[Defect] = field(default_factory=list)
    _seq: int = 0

    def next_id(self) -> str:
        self._seq += 1
        return f"UJ-DEFECT-{self._seq:04d}"

    def add(self, **kwargs: Any) -> Defect:
        d = Defect(id=self.next_id(), **kwargs)
        if d.severity not in SEVERITIES:
            raise ValueError(f"bad severity {d.severity}")
        self.defects.append(d)
        return d

    def open_digital_u0_u1(self) -> list[Defect]:
        return [
            d
            for d in self.defects
            if d.classification == "DIGITAL" and d.severity in ("U0", "U1") and d.status == "OPEN"
        ]

    def counts(self) -> dict[str, int]:
        out = {s: 0 for s in SEVERITIES}
        for d in self.defects:
            out[d.severity] = out.get(d.severity, 0) + 1
        return out

    def write(self) -> Path:
        art = self.root / "artifacts" / "phase_xi"
        art.mkdir(parents=True, exist_ok=True)
        path = art / "DEFECT_REGISTER.json"
        payload = {
            "schema": "gunnchos.uj_defect_register.v1",
            "defects": [d.to_dict() for d in self.defects],
            "counts": self.counts(),
            "open_digital_u0_u1": [d.id for d in self.open_digital_u0_u1()],
        }
        text = json.dumps(payload, indent=2) + chr(10)
        path.write_text(text, encoding="utf-8")
        reports = self.root / "user_journeys" / "reports" / "DEFECT_REGISTER.json"
        reports.write_text(text, encoding="utf-8")
        return path
