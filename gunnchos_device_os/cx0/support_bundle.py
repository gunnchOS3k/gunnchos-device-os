"""Support/diagnostics bundle schema with redaction (CX0 scaffold)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
import json
import re
import time
import uuid


_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_TOKEN = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+")


def redact_text(text: str) -> str:
    text = _EMAIL.sub("[REDACTED_EMAIL]", text)
    text = _TOKEN.sub(r"\1[REDACTED_TOKEN]", text)
    return text


@dataclass
class SupportBundleBuilder:
    redaction_profile: str = "strict"
    artifacts: Dict[str, str] = field(default_factory=dict)

    def add_text_artifact(self, name: str, content: str) -> None:
        self.artifacts[name] = redact_text(content)

    def build(self, out_dir: Path) -> dict:
        out_dir.mkdir(parents=True, exist_ok=True)
        bundle_id = str(uuid.uuid4())
        written: List[str] = []
        for name, content in self.artifacts.items():
            path = out_dir / name
            path.write_text(content)
            written.append(name)
        meta = {
            "bundle_id": bundle_id,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "redaction_profile": self.redaction_profile,
            "artifacts": written,
            "contains_pii": False,
            "claim_boundary": "scaffold_bundle_not_product_support_ux",
        }
        (out_dir / "SUPPORT_BUNDLE.json").write_text(json.dumps(meta, indent=2) + "\n")
        return meta
