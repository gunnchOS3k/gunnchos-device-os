#!/usr/bin/env python3
"""Stream A sample memo — create/edit dogfood app for package pipeline.

Supports:
  create <title>   write a new memo JSON
  edit <title> <text...>  append/replace body
  show <title>     print memo
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def _data_dir() -> Path:
    return Path(os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR", "."))


def _memo_path(title: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in title.strip()) or "untitled"
    return _data_dir() / f"{safe}.memo.json"


def cmd_create(title: str) -> dict:
    path = _memo_path(title)
    if path.exists():
        return {"ok": False, "error": "already_exists", "path": str(path)}
    memo = {
        "title": title,
        "body": "",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "app_id": os.environ.get("GUNNCHOS_APP_ID", "gunnchos.stream_a_sample_memo"),
        "app_version": os.environ.get("GUNNCHOS_APP_VERSION"),
        "revisions": 1,
    }
    path.write_text(json.dumps(memo, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "action": "create", "path": str(path), "memo": memo}


def cmd_edit(title: str, body: str) -> dict:
    path = _memo_path(title)
    if not path.exists():
        created = cmd_create(title)
        if not created.get("ok"):
            return created
    memo = json.loads(path.read_text(encoding="utf-8"))
    memo["body"] = body
    memo["updated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    memo["revisions"] = int(memo.get("revisions") or 1) + 1
    path.write_text(json.dumps(memo, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "action": "edit", "path": str(path), "memo": memo}


def cmd_show(title: str) -> dict:
    path = _memo_path(title)
    if not path.exists():
        return {"ok": False, "error": "missing", "path": str(path)}
    memo = json.loads(path.read_text(encoding="utf-8"))
    return {"ok": True, "action": "show", "path": str(path), "memo": memo}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        # Default dogfood path: create then edit once.
        r1 = cmd_create("stream_a_hello")
        r2 = cmd_edit("stream_a_hello", "Created via STREAM-A-PKT-001 dogfood path.")
        out = {"ok": bool(r1.get("ok") and r2.get("ok")), "steps": [r1, r2]}
        print(json.dumps(out))
        return 0 if out["ok"] else 1

    cmd = argv[0]
    if cmd == "create":
        title = argv[1] if len(argv) > 1 else "untitled"
        result = cmd_create(title)
    elif cmd == "edit":
        title = argv[1] if len(argv) > 1 else "untitled"
        body = " ".join(argv[2:]) if len(argv) > 2 else ""
        result = cmd_edit(title, body)
    elif cmd == "show":
        title = argv[1] if len(argv) > 1 else "untitled"
        result = cmd_show(title)
    else:
        result = {"ok": False, "error": f"unknown_cmd:{cmd}"}
    print(json.dumps(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
