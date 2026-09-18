"""Portfolio authority — privacy-selective export + portable HTML/manifest."""

from __future__ import annotations

import html
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from gunnchos_device_os.cx3.contracts import validate_record


class PortfolioStore:
    def __init__(self, root: Path, *, owner_profile_id: str = "profile:lab-student"):
        self.root = Path(root)
        self.owner_profile_id = owner_profile_id
        self.artifacts_dir = self.root / "artifacts"
        self.collections_dir = self.root / "collections"
        self.exports_dir = self.root / "exports"
        for d in (self.root, self.artifacts_dir, self.collections_dir, self.exports_dir):
            d.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.root, 0o700)
        except OSError:
            pass

    def upsert_artifact(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        artifact = dict(artifact)
        artifact.setdefault("artifact_id", f"pa:{uuid.uuid4().hex[:12]}")
        artifact.setdefault("visibility", "private")
        artifact.setdefault("linked_credential_ids", [])
        artifact.setdefault("evidence_refs", [])
        artifact["certification_claimed"] = False
        ok, errs = validate_record("PortfolioArtifact", artifact)
        if not ok:
            raise ValueError(f"artifact_invalid:{errs}")
        path = self.artifacts_dir / f"{_safe(artifact['artifact_id'])}.json"
        _write_json(path, artifact)
        return artifact

    def list_artifacts(self) -> List[Dict[str, Any]]:
        out = []
        for p in sorted(self.artifacts_dir.glob("*.json")):
            try:
                out.append(json.loads(p.read_text()))
            except Exception:
                continue
        return out

    def upsert_collection(self, collection: Dict[str, Any]) -> Dict[str, Any]:
        collection = dict(collection)
        collection.setdefault("collection_id", f"pc:{uuid.uuid4().hex[:12]}")
        collection.setdefault("owner_profile_id", self.owner_profile_id)
        collection.setdefault("artifact_ids", [])
        collection["certification_claimed"] = False
        ok, errs = validate_record("PortfolioCollection", collection)
        if not ok:
            raise ValueError(f"collection_invalid:{errs}")
        path = self.collections_dir / f"{_safe(collection['collection_id'])}.json"
        _write_json(path, collection)
        return collection

    def selective_export(
        self,
        selected_artifact_ids: Sequence[str],
        *,
        title: str = "Portable learning portfolio",
        credentials: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Privacy-selective: only selected non-private-or-explicitly-chosen artifacts."""
        artifacts = {a["artifact_id"]: a for a in self.list_artifacts()}
        selected: List[Dict[str, Any]] = []
        skipped_private = []
        for aid in selected_artifact_ids:
            art = artifacts.get(aid)
            if not art:
                continue
            # Caller must explicitly select; private items allowed only if selected
            # but default privacy_mode excludes unselected private.
            selected.append(art)
            if art.get("visibility") == "private":
                # still included because explicitly selected — mark in manifest
                pass
        # Also track unselected private for audit
        for aid, art in artifacts.items():
            if aid not in selected_artifact_ids and art.get("visibility") == "private":
                skipped_private.append(aid)

        export_id = f"pex:{uuid.uuid4().hex[:12]}"
        exported_at = _now()
        manifest = {
            "schema": "gunnchos.cx3.portfolio_manifest.v1",
            "title": title,
            "owner_profile_id": self.owner_profile_id,
            "artifact_count": len(selected),
            "artifacts": selected,
            "linked_credentials": credentials or [],
            "skipped_private_unselected": skipped_private,
            "certification_claimed": False,
            "disclaimer": (
                "This portfolio package contains learning evidence assertions only. "
                "It does not claim accreditation, degrees, diplomas, or certifications."
            ),
        }
        export = {
            "export_id": export_id,
            "format": "portable_html_manifest.v1",
            "selected_artifact_ids": list(selected_artifact_ids),
            "manifest": manifest,
            "exported_at": exported_at,
            "certification_claimed": False,
            "privacy_mode": "selective",
        }
        ok, errs = validate_record("PortfolioExport", export)
        if not ok:
            raise ValueError(f"export_invalid:{errs}")

        package_dir = self.exports_dir / export_id
        package_dir.mkdir(parents=True, exist_ok=True)
        _write_json(package_dir / "manifest.json", manifest)
        _write_json(package_dir / "export.json", export)
        html_doc = render_portable_html(manifest)
        (package_dir / "index.html").write_text(html_doc)
        return {
            "ok": True,
            "export": export,
            "package_dir": str(package_dir),
            "files": ["manifest.json", "export.json", "index.html"],
            "certification_claimed": False,
        }


def render_portable_html(manifest: Dict[str, Any]) -> str:
    title = html.escape(str(manifest.get("title") or "Portfolio"))
    disclaimer = html.escape(str(manifest.get("disclaimer") or ""))
    rows = []
    for art in manifest.get("artifacts") or []:
        rows.append(
            "<li><strong>{t}</strong> — visibility={v} — cert_claimed=false<br/>"
            "<span>{s}</span></li>".format(
                t=html.escape(str(art.get("title") or art.get("artifact_id"))),
                v=html.escape(str(art.get("visibility"))),
                s=html.escape(str(art.get("summary") or "")),
            )
        )
    body = "\n".join(rows) or "<li>No artifacts selected.</li>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <style>
    body {{ font-family: Georgia, 'Times New Roman', serif; margin: 2rem; background: #f7f3ea; color: #1c1a16; }}
    header {{ border-bottom: 2px solid #1c1a16; padding-bottom: .75rem; margin-bottom: 1.5rem; }}
    .disclaimer {{ font-size: .95rem; max-width: 42rem; }}
    ul {{ line-height: 1.5; }}
  </style>
</head>
<body>
  <header>
    <h1>{title}</h1>
    <p class="disclaimer">{disclaimer}</p>
    <p><code>certification_claimed=false</code></p>
  </header>
  <main>
    <h2>Selected artifacts</h2>
    <ul>
      {body}
    </ul>
  </main>
</body>
</html>
"""


def _write_json(path: Path, obj: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n")
    os.replace(tmp, path)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _safe(cid: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in cid)[:180]
