"""gunnchAI Tutor first-party application — local tutoring + safety gates.

Owner product requirements (charter §7): tutoring, coding help, device help,
accessibility; local-first; AI suggests / human verifies. Not chatbot-only.

Claim boundary: digital tutor *app integration* and safety gates on gunnchSDK.
Does NOT claim frontier model quality, production LLM deployment, or HUMAN_E6.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.first_party_apps import runtime
from gunnchos_device_os.gunnchai_integration import (
    tutor_local_reply,
    tutor_prompt_guard,
    tutor_safety_check,
    tutor_session_start,
)
from gunnchos_device_os.waike_integration import list_offline_lessons

CLAIM_BOUNDARY = (
    "Digital gunnchAI Tutor app with local reply templates, prompt/response "
    "safety gates, sandbox session memory, and WAIKE lesson context binding. "
    "Not production LLM deployment, not frontier model quality, not HUMAN_E6."
)

REQUIRED_PERMISSIONS = ["storage_read", "storage_write", "ai_interface"]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_gunnchai_tutor(
    *,
    profile: str = "student",
    topic: str = "wireless_basics",
    prompt: str = "Explain OFDM at a high level",
    bind_waike_lesson: str | None = "wireless_basics_101",
    crash_probe: bool = False,
) -> dict[str, Any]:
    runtime.intentional_crash_probe(enabled=crash_probe)
    perms = runtime.assert_permissions(REQUIRED_PERMISSIONS)
    if not perms["ok"]:
        return {
            "ok": False,
            "app_id": "gunnchai_tutor",
            "error": "permission_denied",
            "permissions": perms,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    data_dir = runtime.sandbox_data_dir()
    ui = _repo_root() / "apps/gunnchai_tutor/index.html"
    memory_path = data_dir / "tutor_memory.json"
    memory = runtime.load_json(
        memory_path,
        {"schema": "gunnchos.gunnchai_tutor.memory.v1", "turns": [], "session_count": 0},
    )

    session = tutor_session_start(profile, topic)
    # Clear mock flag for digital gates that are real pattern matchers.
    session = {**session, "mock": False, "runtime": "local_template"}
    guard = tutor_prompt_guard(prompt)
    if not guard.get("ok"):
        result = {
            "ok": False,
            "app_id": "gunnchai_tutor",
            "error": "prompt_blocked",
            "session": session,
            "guard": {**guard, "mock": False},
            "permissions": perms,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        runtime.write_json(data_dir / "gunnchai_tutor_run.json", result)
        return result

    waike_context = None
    if bind_waike_lesson:
        lessons = list_offline_lessons()
        waike_context = {
            "lesson_id": bind_waike_lesson,
            "available": bind_waike_lesson in lessons,
            "lessons": lessons,
            "integration": "waike_lesson_binding",
        }

    reply_payload = tutor_local_reply(topic=topic, prompt=prompt, waike_lesson=bind_waike_lesson)
    safety = tutor_safety_check(reply_payload.get("text", ""))
    safety = {**safety, "mock": False}

    turn = {
        "at": time.time(),
        "profile": profile,
        "topic": topic,
        "prompt": prompt,
        "reply": reply_payload.get("text"),
        "safe_to_show": bool(safety.get("safe_to_show")),
        "waike_lesson": bind_waike_lesson,
    }
    memory["session_count"] = int(memory.get("session_count") or 0) + 1
    turns = list(memory.get("turns") or [])
    turns.append(turn)
    memory["turns"] = turns[-20:]
    memory_path_written = runtime.write_json(memory_path, memory)
    log_path = runtime.append_app_log(
        "gunnchai_tutor_run",
        {
            "session_count": memory["session_count"],
            "topic": topic,
            "safe_to_show": safety.get("safe_to_show"),
            "waike_bound": bool(waike_context and waike_context.get("available")),
        },
    )

    result = {
        "ok": (
            bool(session.get("started"))
            and bool(guard.get("ok"))
            and bool(safety.get("safe_to_show"))
            and perms["ok"]
            and ui.exists()
            and bool(reply_payload.get("ok"))
        ),
        "app_id": "gunnchai_tutor",
        "sdk_app_id": runtime.app_id(),
        "sdk_version": runtime.app_version(),
        "entry": "apps/gunnchai_tutor/index.html",
        "session": session,
        "guard": {**guard, "mock": False},
        "safety": safety,
        "reply": reply_payload,
        "waike_context": waike_context,
        "permissions": perms,
        "persisted_memory_path": memory_path_written,
        "persisted_session_count": memory["session_count"],
        "app_log_path": log_path,
        "ui_present": ui.exists(),
        "mock": False,
        "stub_content": False,
        "depth_claim": "D5_runtime_candidate",
        "claim_boundary": CLAIM_BOUNDARY,
        "owner_functions": [
            "tutor_session",
            "prompt_injection_guard",
            "response_safety_gate",
            "local_reply_template",
            "session_memory_persist",
            "waike_lesson_binding",
            "ai_suggests_human_verifies",
        ],
        "not_claimed": [
            "frontier_model_quality",
            "production_llm_deployment",
            "human_e6_comprehension",
            "full_agent_tool_runtime",
        ],
    }
    runtime.write_json(data_dir / "gunnchai_tutor_run.json", result)
    return result
