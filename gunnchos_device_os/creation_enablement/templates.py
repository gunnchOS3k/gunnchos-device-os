"""STREAM-A-PKT-002 creator templates — instantiate, manifest, build/lint, tests, package metadata.

Full guest E2E is NOT required for every template in this packet; the sample memo
guest chain covers end-to-end. Templates prove scaffold quality on host.
"""
from __future__ import annotations

import json
import py_compile
import shutil
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.release_engineering.sdk.manifest import validate_manifest
from gunnchos_device_os.release_engineering.sdk.packager import PackageBuilder

PACKET = "STREAM-A-PKT-002"

TEMPLATE_SPECS: list[dict[str, Any]] = [
    {
        "id": "application",
        "app_id": "gunnchos.template.application",
        "runtime": "python",
        "permissions": ["storage_read", "storage_write"],
        "entrypoint": "main.py",
        "body": 'print("template.application")\n',
    },
    {
        "id": "cli",
        "app_id": "gunnchos.template.cli",
        "runtime": "python",
        "permissions": ["storage_read"],
        "entrypoint": "main.py",
        "body": 'import sys\nprint({"ok": True, "argv": sys.argv[1:]})\n',
    },
    {
        "id": "python",
        "app_id": "gunnchos.template.python",
        "runtime": "python",
        "permissions": ["storage_read", "storage_write"],
        "entrypoint": "main.py",
        "body": 'def main():\n    return {"ok": True}\n\nif __name__ == "__main__":\n    print(main())\n',
    },
    {
        "id": "web",
        "app_id": "gunnchos.template.web",
        "runtime": "python",
        "permissions": ["storage_read", "network"],
        "entrypoint": "main.py",
        "body": (
            'from http.server import BaseHTTPRequestHandler, HTTPServer\n'
            "class H(BaseHTTPRequestHandler):\n"
            "    def do_GET(self):\n"
            "        self.send_response(200); self.end_headers(); self.wfile.write(b'ok')\n"
            "def main():\n"
            "    return {'ok': True, 'note': 'scaffold only — not a long-running server claim'}\n"
            "if __name__ == '__main__':\n"
            "    print(main())\n"
        ),
    },
    {
        "id": "godot",
        "app_id": "gunnchos.template.godot",
        "runtime": "python",
        "permissions": ["storage_read"],
        "entrypoint": "main.py",
        "body": (
            'print({"ok": True, "runtime_note": "Godot project stub; SILICON_EXACT_EMULATION=false"})\n'
        ),
        "extra_files": {
            "godot/project.godot": "; Engine stub for template packaging metadata\nconfig_version=5\n"
        },
    },
    {
        "id": "ai_skill_agent",
        "app_id": "gunnchos.template.ai_skill_agent",
        "runtime": "python",
        "permissions": ["storage_read", "ai_interface"],
        "entrypoint": "main.py",
        "body": 'print({"ok": True, "skill": "echo", "mode": "local_offline"})\n',
        "capabilities_required": ["ai.invoke"],
    },
    {
        "id": "waike_lab",
        "app_id": "gunnchos.template.waike_lab",
        "runtime": "python",
        "permissions": ["storage_read", "storage_write"],
        "entrypoint": "main.py",
        "body": 'print({"ok": True, "lab": "waike_scaffold", "mastery_claim": False})\n',
    },
    {
        "id": "research_experiment",
        "app_id": "gunnchos.template.research_experiment",
        "runtime": "python",
        "permissions": ["storage_read", "storage_write"],
        "entrypoint": "main.py",
        "body": 'print({"ok": True, "experiment": "scaffold", "EXTERNAL_REPRODUCTION": False})\n',
    },
]


def _manifest_for(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "gunnchos.sdk.app_manifest.v1",
        "app_id": spec["app_id"],
        "name": f"Template {spec['id']}",
        "version": "0.1.0",
        "api_version": "1.0.0",
        "min_os_version": "0.1.0",
        "max_os_version": None,
        "arch_targets": ["aarch64", "x86_64"],
        "entrypoint": spec["entrypoint"],
        "permissions": spec["permissions"],
        "capabilities_required": spec.get("capabilities_required")
        or ["storage.read"],
        "dependencies": [],
        "sandbox_profile": {
            "network_policy": "deny_all" if "network" not in spec["permissions"] else "allowlist",
            "filesystem_scope": f"/data/apps/{spec['app_id']}",
            "allow_ipc": False,
        },
        "runtime": spec["runtime"],
        "stub_content": False,
        "source": f"sdk/templates/{spec['id']}",
        "stream_packet": PACKET,
        "template_kind": spec["id"],
    }


def materialize_templates(repo_root: Path) -> dict[str, Any]:
    root = repo_root / "sdk" / "templates"
    root.mkdir(parents=True, exist_ok=True)
    created = []
    for spec in TEMPLATE_SPECS:
        app_dir = root / spec["id"]
        if app_dir.exists():
            shutil.rmtree(app_dir)
        app_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / "main.py").write_text(spec["body"], encoding="utf-8")
        (app_dir / "manifest.json").write_text(
            json.dumps(_manifest_for(spec), indent=2) + "\n", encoding="utf-8"
        )
        (app_dir / "README.md").write_text(
            f"# Template: {spec['id']}\n\nScaffold for STREAM-A-PKT-002. Not a shipping claim.\n",
            encoding="utf-8",
        )
        for rel, content in (spec.get("extra_files") or {}).items():
            path = app_dir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        created.append(spec["id"])
    return {"ok": True, "templates": created, "root": str(root)}


def run_template_suite(repo_root: Path) -> dict[str, Any]:
    started = time.time()
    materialize = materialize_templates(repo_root)
    work = repo_root / "artifacts" / "stream_a_pkt_002" / "template_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)
    builder = PackageBuilder(repo_root)
    rows: list[dict[str, Any]] = []

    for spec in TEMPLATE_SPECS:
        app_dir = repo_root / "sdk" / "templates" / spec["id"]
        row: dict[str, Any] = {"id": spec["id"], "app_id": spec["app_id"]}
        manifest = json.loads((app_dir / "manifest.json").read_text(encoding="utf-8"))
        failures = validate_manifest(manifest)
        row["manifest_ok"] = not failures
        row["manifest_failures"] = failures
        try:
            py_compile.compile(str(app_dir / "main.py"), doraise=True)
            row["lint_ok"] = True
        except Exception as exc:  # noqa: BLE001
            row["lint_ok"] = False
            row["lint_error"] = str(exc)
        # Minimal test: entrypoint exists + permissions non-empty
        row["tests_ok"] = bool(manifest.get("permissions")) and (app_dir / "main.py").exists()
        build = builder.build(app_dir, work / "packages", sign=False)
        row["package_ok"] = bool(build.get("ok"))
        row["package_metadata"] = {
            "version": build.get("version"),
            "package_digest": build.get("package_digest"),
            "file_count": build.get("file_count"),
            "permissions": manifest.get("permissions"),
        }
        row["ok"] = all(
            row[k] for k in ("manifest_ok", "lint_ok", "tests_ok", "package_ok")
        )
        rows.append(row)

    result = {
        "schema": "gunnchos.creation_enablement.templates.v1",
        "packet": PACKET,
        "materialize": materialize,
        "templates": rows,
        "ok": all(r["ok"] for r in rows) and len(rows) == len(TEMPLATE_SPECS),
        "count": len(rows),
        "duration_ms": int((time.time() - started) * 1000),
        "completed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "claim_boundary": (
            "Host scaffold instantiate/manifest/lint/test/package-metadata only. "
            "Does not by itself earn CREATOR_END_TO_END_DIGITAL_PASS."
        ),
    }
    out = repo_root / "artifacts" / "stream_a_pkt_002" / "TEMPLATE_SUITE_RESULT.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    print(json.dumps(run_template_suite(root), indent=2))
