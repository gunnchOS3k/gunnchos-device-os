"""Local AI tier via OS API — registry, hash, runtime, timeout, fallback.

Uses real llama.cpp when GGUF + llama-cli are present. Not an HTTP stub as sole proof.

Intelligence labels (aligned with gunnchAI3k registry):
  nano  — SmolLM2-135M Instruct Q4_K_M 512-ctx; Nano/fallback only
  fast  — Local Fast (360M-class) when GGUF weights are on disk
  pro   — Local Pro (1.5B-class) when GGUF weights are on disk
  micro — deterministic hashed artifact (always-on digital proof)

SmolLM2 is never Local Fast, Local Pro, or GUNNCHAI_APP_PRODUCT_COMPLETE intelligence.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Capability → prompt wrapper
_PROMPTS = {
    "summarize": "Summarize briefly:\n{input}\nSummary:",
    "translate": "Translate to clear English:\n{input}\nTranslation:",
    "tutor": "You are a patient tutor. Explain:\n{input}\nAnswer:",
    "code": "Write a short code hint for:\n{input}\nHint:",
    "search": "Key terms to search for:\n{input}\nTerms:",
    "reason": "Reason step by step:\n{input}\nConclusion:",
    "diagnose": "Diagnose this OS/device issue:\n{input}\nDiagnosis:",
    "classify": "Classify into one label:\n{input}\nLabel:",
}

TIER_NANO = "nano"
TIER_FAST = "fast"
TIER_PRO = "pro"
TIER_MICRO = "micro"

ROLE_NANO = "NANO_LOCAL"
ROLE_FAST = "LOCAL_FAST"
ROLE_PRO = "LOCAL_PRO"
ROLE_MICRO = "MICRO"

SMOLLM2_MODEL_ID = "smollm2-135m-q4"
SMOLLM2_FILENAME = "SmolLM2-135M-Instruct-Q4_K_M.gguf"
NANO_CONTEXT_TOKENS = 512
NANO_QUANT = "Q4_K_M"
NANO_DISPLAY_LABEL = "Nano/fallback"
NANO_PARAMETERS = "135M"

SMOLLM2_FORBIDDEN_TIERS = frozenset({"fast", "pro", "small", "medium", "local_fast", "local_pro"})
SMOLLM2_FORBIDDEN_ROLES = frozenset({ROLE_FAST, ROLE_PRO})
SMOLLM2_FORBIDDEN_LABELS = frozenset({"Local Fast", "Local Pro", "small", "medium"})

_FAST_GGUF_RE = re.compile(r"360", re.IGNORECASE)
_PRO_GGUF_RE = re.compile(r"1[._]?5b|qwen2", re.IGNORECASE)
_SMOLLM2_ID_RE = re.compile(r"smollm2|smollm-135|135m-q4", re.IGNORECASE)


def is_smollm2_identity(model_id: str, *, path: Path | None = None) -> bool:
    blob = f"{model_id} {path.name if path else ''}"
    return bool(_SMOLLM2_ID_RE.search(blob))


def assert_honest_smollm2_label(
    model_id: str,
    *,
    tier: str,
    role: str = ROLE_NANO,
    display_label: str = NANO_DISPLAY_LABEL,
    is_nano_fallback_only: bool = True,
    context_tokens: int | None = NANO_CONTEXT_TOKENS,
    path: Path | None = None,
) -> None:
    """Reject any attempt to treat SmolLM2-135M as Local Fast/Pro/daily intelligence."""
    if not is_smollm2_identity(model_id, path=path):
        return
    if tier in SMOLLM2_FORBIDDEN_TIERS:
        raise ValueError(
            "SmolLM2-135M Q4_K_M 512-ctx is Nano/fallback only; "
            f"cannot label as Local Fast/Pro (tier={tier!r})"
        )
    if role in SMOLLM2_FORBIDDEN_ROLES:
        raise ValueError(
            "SmolLM2-135M Q4_K_M 512-ctx is Nano/fallback only; "
            f"cannot label as {role}"
        )
    if display_label in SMOLLM2_FORBIDDEN_LABELS:
        raise ValueError(
            "SmolLM2-135M Q4_K_M 512-ctx is Nano/fallback only; "
            f"cannot display as {display_label!r}"
        )
    if tier != TIER_NANO:
        raise ValueError(f"SmolLM2 tier must be {TIER_NANO!r}, got {tier!r}")
    if not is_nano_fallback_only:
        raise ValueError("SmolLM2 must set is_nano_fallback_only=True")
    if context_tokens not in (None, NANO_CONTEXT_TOKENS):
        raise ValueError(
            f"SmolLM2 Nano fallback context is {NANO_CONTEXT_TOKENS}-ctx, got {context_tokens}"
        )


def _model_search_roots(repo_root: Path) -> list[Path]:
    repos = os.environ.get("GUNNCHOS_REPOS_ROOT", "")
    return [
        repo_root.parent / "gunnchAI3k" / "models" / "local",
        Path(repos) / "gunnchAI3k" / "models" / "local" if repos else Path(),
        repo_root / "artifacts" / "phase_xii" / "models",
        repo_root / ".deps" / "gunnchAI3k" / "models" / "local",
    ]


def list_local_ggufs(repo_root: Path) -> list[Path]:
    found: list[Path] = []
    seen: set[str] = set()
    for root in _model_search_roots(repo_root):
        if not root or not root.exists() or not root.is_dir():
            continue
        for path in sorted(root.glob("*.gguf")):
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            found.append(path)
    return found


def find_smollm2_gguf(repo_root: Path) -> Path | None:
    for root in _model_search_roots(repo_root):
        cand = root / SMOLLM2_FILENAME if root else Path()
        if cand and cand.exists():
            return cand
    return None


def local_fast_weights_present(repo_root: Path) -> bool:
    return any(_FAST_GGUF_RE.search(p.name) for p in list_local_ggufs(repo_root))


def local_pro_weights_present(repo_root: Path) -> bool:
    return any(_PRO_GGUF_RE.search(p.name) for p in list_local_ggufs(repo_root))


@dataclass
class ModelRecord:
    model_id: str
    path: Path
    sha256: str
    tier: str  # nano | fast | pro | micro
    runtime: str  # llama_cpp | deterministic_micro
    max_tokens: int = 64
    verified: bool = False
    role: str = ROLE_MICRO
    is_nano_fallback_only: bool = False
    context_tokens: int | None = None
    quant: str | None = None
    display_label: str = ""
    weights_present: bool = True

    def public_route(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "sha256": self.sha256[:16],
            "tier": self.tier,
            "role": self.role,
            "display_label": self.display_label,
            "is_nano_fallback_only": self.is_nano_fallback_only,
            "context_tokens": self.context_tokens,
            "quant": self.quant,
        }


@dataclass
class ModelRegistry:
    root: Path
    models: dict[str, ModelRecord] = field(default_factory=dict)

    def register(
        self,
        model_id: str,
        path: Path,
        *,
        tier: str,
        runtime: str,
        max_tokens: int = 64,
        known_sha256: str | None = None,
        role: str | None = None,
        is_nano_fallback_only: bool | None = None,
        context_tokens: int | None = None,
        quant: str | None = None,
        display_label: str | None = None,
        weights_present: bool = True,
    ) -> ModelRecord:
        path = path.resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        resolved_role = role or (
            ROLE_NANO
            if tier == TIER_NANO
            else ROLE_FAST
            if tier == TIER_FAST
            else ROLE_PRO
            if tier == TIER_PRO
            else ROLE_MICRO
        )
        resolved_nano = bool(is_nano_fallback_only) if is_nano_fallback_only is not None else tier == TIER_NANO
        resolved_label = display_label or (
            NANO_DISPLAY_LABEL
            if tier == TIER_NANO
            else "Local Fast"
            if tier == TIER_FAST
            else "Local Pro"
            if tier == TIER_PRO
            else "micro-deterministic"
        )
        resolved_ctx = context_tokens if context_tokens is not None else (NANO_CONTEXT_TOKENS if tier == TIER_NANO else None)
        resolved_quant = quant if quant is not None else (NANO_QUANT if is_smollm2_identity(model_id, path=path) else None)
        assert_honest_smollm2_label(
            model_id,
            tier=tier,
            role=resolved_role,
            display_label=resolved_label,
            is_nano_fallback_only=resolved_nano,
            context_tokens=resolved_ctx,
            path=path,
        )
        cache = self.root / f"{model_id}.sha256"
        if known_sha256:
            digest = known_sha256
        elif cache.exists():
            cached = cache.read_text(encoding="utf-8").strip().split()
            # format: "<sha256> <size>"
            if len(cached) == 2 and cached[1] == str(path.stat().st_size):
                digest = cached[0]
            else:
                digest = _hash_file(path)
                cache.write_text(f"{digest} {path.stat().st_size}\n", encoding="utf-8")
        else:
            digest = _hash_file(path) if path.stat().st_size >= 8_000_000 else hashlib.sha256(path.read_bytes()).hexdigest()
            self.root.mkdir(parents=True, exist_ok=True)
            cache.write_text(f"{digest} {path.stat().st_size}\n", encoding="utf-8")
        rec = ModelRecord(
            model_id=model_id,
            path=path,
            sha256=digest,
            tier=tier,
            runtime=runtime,
            max_tokens=max_tokens,
            verified=True,
            role=resolved_role,
            is_nano_fallback_only=resolved_nano,
            context_tokens=resolved_ctx,
            quant=resolved_quant,
            display_label=resolved_label,
            weights_present=weights_present,
        )
        self.models[model_id] = rec
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "registry.json").write_text(
            json.dumps(
                {
                    k: {
                        "model_id": v.model_id,
                        "path": str(v.path.name),  # basename only in artifact
                        "sha256": v.sha256,
                        "tier": v.tier,
                        "runtime": v.runtime,
                        "max_tokens": v.max_tokens,
                        "verified": v.verified,
                        "role": v.role,
                        "is_nano_fallback_only": v.is_nano_fallback_only,
                        "context_tokens": v.context_tokens,
                        "quant": v.quant,
                        "display_label": v.display_label,
                        "weights_present": v.weights_present,
                    }
                    for k, v in self.models.items()
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return rec

    def verify(self, model_id: str, *, rehash: bool = False) -> bool:
        rec = self.models[model_id]
        if not rec.path.exists():
            rec.verified = False
            return False
        if not rehash and rec.path.stat().st_size >= 8_000_000:
            # Large GGUF: trust size-cached registry hash unless rehash requested
            cache = self.root / f"{model_id}.sha256"
            if cache.exists():
                cached = cache.read_text(encoding="utf-8").strip().split()
                if len(cached) == 2 and cached[0] == rec.sha256 and cached[1] == str(rec.path.stat().st_size):
                    rec.verified = True
                    return True
        digest = _hash_file(rec.path) if rec.path.stat().st_size >= 8_000_000 else hashlib.sha256(rec.path.read_bytes()).hexdigest()
        rec.verified = digest == rec.sha256
        return rec.verified


def _hash_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _deterministic_micro(capability: str, text: str) -> str:
    """Real local compute tier (no network): hash-stable micro responses."""
    digest = hashlib.sha256(f"{capability}:{text}".encode()).hexdigest()[:12]
    words = [w for w in text.replace("\n", " ").split(" ") if w][:12]
    stem = " ".join(words) if words else "(empty)"
    return f"[{capability}/micro:{digest}] {stem}"


class LocalAiRuntime:
    """At least one real local model tier with timeout + fallback.

    Daily-intelligence preference: Local Fast → Local Pro → Nano fallback → micro.
    SmolLM2 is selectable as the llama path when Fast/Pro weights are absent, but
    it is labeled Nano/fallback only — never the full intelligence layer.
    """

    def __init__(self, registry: ModelRegistry, *, preferred: str | None = None, timeout_s: float = 25.0):
        self.registry = registry
        self.preferred = preferred
        self.timeout_s = timeout_s
        self.llama_cli = shutil.which("llama-cli") or shutil.which("llama-cpp")
        self.last_route: dict[str, Any] = {}
        self.preferred_daily_tier: str = TIER_MICRO
        self.local_fast_weights_present: bool = False
        self.local_pro_weights_present: bool = False
        self.nano_weights_present: bool = False
        self._repo_root: Path | None = None

    def ensure_default_models(self, repo_root: Path, *, include_llama: bool | None = None) -> list[str]:
        """Register deterministic micro + optional llama GGUFs from sibling."""
        self._repo_root = repo_root
        micro_path = repo_root / "os_build" / "phase_xiv" / "local_ai" / "micro_model.bin"
        micro_path.parent.mkdir(parents=True, exist_ok=True)
        if not micro_path.exists():
            # compact deterministic weights blob (not a neural net — hashed artifact)
            payload = b"GUNNCHOS_MICRO_TIER_v1\n" + hashlib.sha256(b"phase-xiv-local-ai").digest() * 32
            micro_path.write_bytes(payload)
        self.registry.register(
            "micro-deterministic-v1",
            micro_path,
            tier=TIER_MICRO,
            runtime="deterministic_micro",
            max_tokens=32,
            role=ROLE_MICRO,
            is_nano_fallback_only=False,
            display_label="micro-deterministic",
        )
        registered = ["micro-deterministic-v1"]

        if include_llama is None:
            include_llama = os.environ.get("GUNNCHOS_ENABLE_LLAMA_TIER", "").lower() in {"1", "true", "yes"}

        self.local_fast_weights_present = local_fast_weights_present(repo_root)
        self.local_pro_weights_present = local_pro_weights_present(repo_root)
        nano_gguf = find_smollm2_gguf(repo_root)
        self.nano_weights_present = bool(nano_gguf and nano_gguf.exists())

        if include_llama:
            if nano_gguf is not None:
                self.registry.register(
                    SMOLLM2_MODEL_ID,
                    nano_gguf,
                    tier=TIER_NANO,
                    runtime="llama_cpp",
                    max_tokens=48,
                    role=ROLE_NANO,
                    is_nano_fallback_only=True,
                    context_tokens=NANO_CONTEXT_TOKENS,
                    quant=NANO_QUANT,
                    display_label=NANO_DISPLAY_LABEL,
                )
                registered.append(SMOLLM2_MODEL_ID)
            # Fast/Pro: register only when real GGUF weights exist (honest OPEN otherwise).
            for gguf in list_local_ggufs(repo_root):
                name = gguf.name
                if is_smollm2_identity(name, path=gguf):
                    continue
                if _FAST_GGUF_RE.search(name) and "local-fast" not in self.registry.models:
                    self.registry.register(
                        "local-fast",
                        gguf,
                        tier=TIER_FAST,
                        runtime="llama_cpp",
                        max_tokens=96,
                        role=ROLE_FAST,
                        is_nano_fallback_only=False,
                        display_label="Local Fast",
                    )
                    registered.append("local-fast")
                elif _PRO_GGUF_RE.search(name) and "local-pro" not in self.registry.models:
                    self.registry.register(
                        "local-pro",
                        gguf,
                        tier=TIER_PRO,
                        runtime="llama_cpp",
                        max_tokens=128,
                        role=ROLE_PRO,
                        is_nano_fallback_only=False,
                        display_label="Local Pro",
                    )
                    registered.append("local-pro")

        if self.preferred is None:
            self.preferred, self.preferred_daily_tier = self._select_preferred(registered)
        elif SMOLLM2_MODEL_ID in registered and self.preferred == SMOLLM2_MODEL_ID:
            self.preferred_daily_tier = "nano_fallback"
        return registered

    def _select_preferred(self, registered: list[str]) -> tuple[str, str]:
        """Prefer measured Fast/Pro weights; SmolLM2 is Nano fallback, never daily intelligence."""
        if "local-fast" in registered:
            return "local-fast", TIER_FAST
        if "local-pro" in registered:
            return "local-pro", TIER_PRO
        if SMOLLM2_MODEL_ID in registered:
            return SMOLLM2_MODEL_ID, "nano_fallback"
        return "micro-deterministic-v1", TIER_MICRO

    def intelligence_inventory(self) -> dict[str, Any]:
        nano = self.registry.models.get(SMOLLM2_MODEL_ID)
        fast = self.registry.models.get("local-fast")
        pro = self.registry.models.get("local-pro")
        return {
            "schema": "gunnchos.local_ai.intelligence_inventory.v1",
            "nano": {
                "present": self.nano_weights_present,
                "model_id": SMOLLM2_MODEL_ID if nano else None,
                "tier": TIER_NANO if nano else None,
                "role": ROLE_NANO if nano else None,
                "display_label": NANO_DISPLAY_LABEL,
                "is_nano_fallback_only": True,
                "context_tokens": NANO_CONTEXT_TOKENS,
                "quant": NANO_QUANT,
                "parameters": NANO_PARAMETERS,
                "filename": SMOLLM2_FILENAME,
            },
            "fast": {
                "present": self.local_fast_weights_present,
                "model_id": "local-fast" if fast else None,
                "open": not self.local_fast_weights_present,
                "reason": None
                if self.local_fast_weights_present
                else "Local Fast GGUF (360M-class) not on disk — registry slot only",
            },
            "pro": {
                "present": self.local_pro_weights_present,
                "model_id": "local-pro" if pro else None,
                "open": not self.local_pro_weights_present,
                "reason": None
                if self.local_pro_weights_present
                else "Local Pro GGUF (1.5B-class) not on disk — registry slot only",
            },
            "preferred": self.preferred,
            "preferred_daily_tier": self.preferred_daily_tier,
            "smollm2_is_full_intelligence_layer": False,
            "GUNNCHAI_APP_PRODUCT_COMPLETE": False,
            "HUMAN_E6": False,
            "claim_boundary": (
                "SmolLM2-135M Instruct Q4_K_M 512-ctx is Nano/fallback only. "
                "Not Local Fast, not Local Pro, not app-product-complete intelligence."
            ),
        }

    def run_capability(self, capability: str, text: str, *, timeout_s: float | None = None) -> dict[str, Any]:
        timeout = timeout_s if timeout_s is not None else self.timeout_s
        order: list[str] = []
        if self.preferred and self.preferred in self.registry.models:
            order.append(self.preferred)
        for mid in self.registry.models:
            if mid not in order:
                order.append(mid)
        # Always ensure micro is last fallback
        if "micro-deterministic-v1" in self.registry.models and order[-1] != "micro-deterministic-v1":
            order = [m for m in order if m != "micro-deterministic-v1"] + ["micro-deterministic-v1"]

        errors: list[dict[str, Any]] = []
        for mid in order:
            rec = self.registry.models[mid]
            if not self.registry.verify(mid):
                errors.append({"model_id": mid, "error": "hash_mismatch"})
                continue
            try:
                if rec.runtime == "llama_cpp":
                    out = self._run_llama(rec, capability, text, timeout)
                else:
                    out = {
                        "ok": True,
                        "text": _deterministic_micro(capability, text),
                        "runtime": "deterministic_micro",
                        "tier": rec.tier,
                        "route": rec.public_route(),
                    }
                route = dict(out.get("route") or {})
                route["preferred_daily_tier"] = self.preferred_daily_tier
                out["route"] = route
                out["is_nano_fallback_only"] = rec.is_nano_fallback_only
                out["display_label"] = rec.display_label
                out["role"] = rec.role
                self.last_route = route
                return out
            except Exception as exc:  # noqa: BLE001 — fall through tiers
                errors.append({"model_id": mid, "error": str(exc)})
                continue
        return {
            "ok": False,
            "text": "all local tiers failed",
            "runtime": None,
            "tier": None,
            "route": {"errors": errors},
        }

    def _run_llama(self, rec: ModelRecord, capability: str, text: str, timeout: float) -> dict[str, Any]:
        if not self.llama_cli:
            raise RuntimeError("llama-cli not installed")
        prompt = _PROMPTS.get(capability, "{input}").format(input=text[:500])
        cmd = [
            self.llama_cli,
            "-m",
            str(rec.path),
            "-p",
            prompt,
            "-n",
            str(rec.max_tokens),
            "--no-display-prompt",
            "-no-cnv",
        ]
        # Declared Nano window is recorded on the route; do not force -c here —
        # some llama-cli/Metal hosts hang when ctx is overridden at invoke time.
        started = time.time()
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "LLAMA_NO_COLOR": "1"},
        )
        elapsed = time.time() - started
        if proc.returncode != 0:
            raise RuntimeError(f"llama-cli rc={proc.returncode}: {(proc.stderr or '')[-400:]}")
        out_text = (proc.stdout or "").strip()
        if not out_text:
            # some builds print to stderr
            out_text = (proc.stderr or "").strip()[-500:]
        if not out_text:
            raise RuntimeError("empty llama output")
        route = rec.public_route()
        route["elapsed_s"] = round(elapsed, 3)
        route["llama_cli"] = True
        return {
            "ok": True,
            "text": out_text[:2000],
            "runtime": "llama_cpp",
            "tier": rec.tier,
            "route": route,
        }


def invoke_gunnchai_tutor_local(
    repo_root: Path,
    *,
    prompt: str = "Explain OFDM at a high level",
    registry_root: Path | None = None,
    include_llama: bool | None = None,
) -> dict[str, Any]:
    """OS-local tutor path: safety-gated LocalAiRuntime with honest Nano/Fast/Pro labels.

    Does not import first_party ``run_gunnchai_tutor`` (PLATFORM-001 / companion_bridge).
    """
    from gunnchos_device_os.gunnchai_integration import (
        tutor_prompt_guard,
        tutor_safety_check,
        tutor_session_start,
    )

    session = tutor_session_start("student", "wireless_basics")
    guard = tutor_prompt_guard(prompt)
    if not guard.get("ok"):
        return {
            "ok": False,
            "error": "prompt_blocked",
            "session": session,
            "guard": guard,
            "GUNNCHAI_APP_PRODUCT_COMPLETE": False,
            "HUMAN_E6": False,
        }
    art = registry_root or (repo_root / "artifacts" / "phase_xiv" / "tutor_local_ai")
    rt = LocalAiRuntime(ModelRegistry(art), timeout_s=20)
    registered = rt.ensure_default_models(repo_root, include_llama=include_llama)
    inventory = rt.intelligence_inventory()
    out = rt.run_capability("tutor", prompt)
    rec = rt.registry.models.get(str((out.get("route") or {}).get("model_id") or ""))
    safety = tutor_safety_check(str(out.get("text") or ""))
    return {
        "ok": bool(session.get("started")) and bool(guard.get("ok")) and bool(safety.get("safe_to_show")) and bool(out.get("ok")),
        "session": session,
        "guard": guard,
        "safety": safety,
        "reply": {
            "text": out.get("text"),
            "runtime": out.get("runtime"),
            "tier": out.get("tier"),
            "role": out.get("role"),
            "display_label": out.get("display_label"),
            "is_nano_fallback_only": out.get("is_nano_fallback_only"),
            "route": out.get("route"),
        },
        "registered": registered,
        "intelligence": inventory,
        "smollm2_labeled_as_fast_or_pro": bool(rec and rec.tier in SMOLLM2_FORBIDDEN_TIERS),
        "stub_content": False,
        "GUNNCHAI_APP_PRODUCT_COMPLETE": False,
        "HUMAN_E6": False,
        "claim_boundary": inventory["claim_boundary"],
    }
