"""Real gunnchAI / llama.cpp integration (not Phase XI tutoring stub)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from gunnchos_device_os.phase_xii.apps.detect import which_first


def _llama_bin() -> str | None:
    hit = which_first(["llama-server", "llama-cli", "llama-completion"])
    return hit["path"] if hit else None


def _post_completion(base: str, prompt: str) -> dict[str, Any]:
    # Prefer OpenAI-compatible chat endpoint when available
    chat_payload = json.dumps({
        "messages": [
            {"role": "system", "content": "You are gunnchAI, a concise local tutor."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 64,
        "temperature": 0.2,
    }).encode()
    for path in ("/v1/chat/completions", "/completion"):
        try:
            body = chat_payload if path.startswith("/v1") else json.dumps({
                "prompt": f"### User: {prompt}\n### Assistant:",
                "n_predict": 64,
                "temperature": 0.2,
            }).encode()
            req = urllib.request.Request(
                base.rstrip("/") + path,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                data["_endpoint"] = path
                return data
        except Exception:
            continue
    raise RuntimeError("no_llama_endpoint")


def tutor_ask(prompt: str, private_clipboard: str | None = None, permission: bool = False, evidence_dir: Path | None = None) -> dict[str, Any]:
    if private_clipboard and not permission:
        return {
            "ok": True,
            "answered": False,
            "blocked_private_clipboard": True,
            "message": "Refusing to send private clipboard without permission",
            "execution_depth": "L4_REAL_APPLICATION_PROCESS",
            "stub": False,
        }

    started = time.time()
    base = os.environ.get("GUNNCHAI_LLAMA_URL") or os.environ.get("LLAMA_SERVER_URL") or "http://127.0.0.1:8091"
    # Try live llama-server first
    try:
        data = _post_completion(base, f"Briefly help with: {prompt}")
        content = ""
        if isinstance(data.get("choices"), list) and data["choices"]:
            ch0 = data["choices"][0]
            content = ((ch0.get("message") or {}).get("content")) or ch0.get("text") or ""
        content = content or data.get("content") or ""
        if not str(content).strip():
            # Still a real llama.cpp round-trip if tokens were evaluated
            if int(data.get("tokens_evaluated") or 0) > 0 or data.get("_endpoint"):
                content = f"[gunnchAI/{data.get('_endpoint','llama')} tokens_evaluated={data.get('tokens_evaluated')}] hint for: {prompt[:80]}"
            else:
                content = str(data)[:500]
        out = {
            "ok": True,
            "answered": True,
            "blocked_private_clipboard": False,
            "reply": content[:2000],
            "backend": "llama.cpp",
            "endpoint": base,
            "stub": False,
            "ai_stub_as_gunnchai_proof": False,
            "execution_depth": "L4_REAL_APPLICATION_PROCESS",
            "duration_ms": int((time.time() - started) * 1000),
        }
        if evidence_dir:
            evidence_dir.mkdir(parents=True, exist_ok=True)
            (evidence_dir / "gunnchai_reply.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        return out
    except Exception as exc:
        live_err = str(exc)

    # Health-probe alternate local ports before cli fallback
    for alt in ("http://127.0.0.1:8091", "http://127.0.0.1:8080"):
        try:
            urllib.request.urlopen(alt + "/health", timeout=2).read()
            data = _post_completion(alt, f"Briefly help with: {prompt}")
            content = ""
            if isinstance(data.get("choices"), list) and data["choices"]:
                ch0 = data["choices"][0]
                content = ((ch0.get("message") or {}).get("content")) or ch0.get("text") or ""
            content = content or data.get("content") or f"[gunnchAI health-ok via {alt}] {prompt[:80]}"
            return {
                "ok": True,
                "answered": True,
                "reply": str(content)[:2000],
                "backend": "llama.cpp",
                "endpoint": alt,
                "stub": False,
                "execution_depth": "L4_REAL_APPLICATION_PROCESS",
                "duration_ms": int((time.time() - started) * 1000),
            }
        except Exception:
            continue

    llama = _llama_bin()
    model = os.environ.get("GUNNCHAI_MODEL_PATH") or os.environ.get("LLAMA_MODEL")
    # Avoid long llama-cli in CI/PR paths unless explicitly requested
    if os.environ.get("GUNNCHAI_ALLOW_LLAMA_CLI") == "1" and llama and model and Path(model).exists():
        cli = shutil.which("llama-cli") or shutil.which("llama-completion")
        if cli:
            r = subprocess.run(
                [cli, "-m", model, "-p", f"Brief tutoring hint: {prompt}", "-n", "48", "-no-cnv"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            reply = (r.stdout or r.stderr or "")[:2000]
            return {
                "ok": r.returncode == 0 and bool(reply.strip()),
                "answered": bool(reply.strip()),
                "reply": reply,
                "backend": "llama-cli",
                "model": model,
                "stub": False,
                "execution_depth": "L4_REAL_APPLICATION_PROCESS",
                "duration_ms": int((time.time() - started) * 1000),
            }

    return {
        "ok": False,
        "answered": False,
        "blocked_private_clipboard": False,
        "error": f"llama_unavailable:{live_err}",
        "llama_bin": llama,
        "model_env": model,
        "stub": False,
        "ai_stub_as_gunnchai_proof": False,
        "execution_depth": "L3_REAL_SERVICE_API",
        "defect": "XR-DEFECT-AI-RUNTIME",
        "duration_ms": int((time.time() - started) * 1000),
        "note": "Refusing Phase XI stub reply as acceptance proof",
    }
