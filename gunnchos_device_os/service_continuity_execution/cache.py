"""NET-ORCH-033 — persistent local cache with fresh-process A→B→C proof."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


class PersistentContinuityCache:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, Any] = {}
        if self.storage_path.exists():
            self._data = json.loads(self.storage_path.read_text(encoding="utf-8"))

    def put(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._flush()

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def keys(self) -> list[str]:
        return sorted(self._data.keys())

    def _flush(self) -> None:
        self.storage_path.write_text(json.dumps(self._data, sort_keys=True, indent=2), encoding="utf-8")


def _write_worker(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "import json, os, sys",
                "from pathlib import Path",
                "sys.path.insert(0, sys.argv[1])",
                "from gunnchos_device_os.service_continuity_execution.cache import PersistentContinuityCache",
                "root = Path(sys.argv[2])",
                "phase = sys.argv[3]",
                "path = root / 'continuity_cache.json'",
                "meta = root / f'meta_{phase}.json'",
                "if phase == 'A':",
                "    if path.exists():",
                "        path.unlink()",
                "    a = PersistentContinuityCache(path)",
                "    a.put('lesson-1', {'title': 'intro', 'bytes': 1200})",
                "    a.put('lesson-2', {'title': 'practice', 'bytes': 800})",
                "    meta.write_text(json.dumps({'pid': os.getpid(), 'keys': a.keys()}), encoding='utf-8')",
                "elif phase == 'B':",
                "    b = PersistentContinuityCache(path)",
                "    hit = b.get('lesson-1')",
                "    b.put('lesson-3', {'title': 'quiz', 'bytes': 400})",
                "    meta.write_text(json.dumps({'pid': os.getpid(), 'keys': b.keys(), 'hit': hit}), encoding='utf-8')",
                "elif phase == 'C':",
                "    c = PersistentContinuityCache(path)",
                "    meta.write_text(json.dumps({",
                "        'pid': os.getpid(),",
                "        'keys': c.keys(),",
                "        'lesson1': c.get('lesson-1'),",
                "    }), encoding='utf-8')",
                "else:",
                "    raise SystemExit('bad phase')",
                "",
            ]
        ),
        encoding="utf-8",
    )


def prove_persistent_cache_a_b_c(storage_dir: Path) -> dict[str, Any]:
    storage_dir = Path(storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[2]
    worker = storage_dir / "_cache_worker.py"
    _write_worker(worker)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")
    pids: dict[str, int] = {}
    for phase in ("A", "B", "C"):
        subprocess.check_call(
            [sys.executable, str(worker), str(repo_root), str(storage_dir), phase],
            env=env,
            cwd=str(repo_root),
        )
        meta = json.loads((storage_dir / f"meta_{phase}.json").read_text(encoding="utf-8"))
        pids[phase] = int(meta["pid"])
    meta_a = json.loads((storage_dir / "meta_A.json").read_text(encoding="utf-8"))
    meta_b = json.loads((storage_dir / "meta_B.json").read_text(encoding="utf-8"))
    meta_c = json.loads((storage_dir / "meta_C.json").read_text(encoding="utf-8"))
    distinct = len(set(pids.values())) == 3
    ok = (
        distinct
        and meta_a["keys"] == ["lesson-1", "lesson-2"]
        and meta_b["hit"] == {"title": "intro", "bytes": 1200}
        and meta_b["keys"] == ["lesson-1", "lesson-2", "lesson-3"]
        and meta_c["keys"] == ["lesson-1", "lesson-2", "lesson-3"]
        and meta_c["lesson1"] == {"title": "intro", "bytes": 1200}
    )
    return {
        "schema": "gunnchos.engineering_wave006.persistent_cache_a_b_c.v1",
        "ok": ok,
        "fresh_process_required": True,
        "distinct_pids": distinct,
        "pids": pids,
        "keys_after_a": meta_a["keys"],
        "keys_after_b": meta_b["keys"],
        "keys_after_c": meta_c["keys"],
        "process_c_lesson1": meta_c["lesson1"],
    }
