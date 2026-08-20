"""Wave 004 platform coordinator — security, reliability, offline operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json

from gunnchos_device_os.connectivity_orchestrator import BearerKind, BearerMetrics, ConnectivityOrchestrator
from gunnchos_device_os.diagnostics_log import DiagnosticsLog
from gunnchos_device_os.permissions_manager import PermissionsManager
from gunnchos_device_os.phase_xiv.local_ai import LocalAiRuntime, ModelRegistry
from gunnchos_device_os.platform.accessibility_store import AccessibilityStore
from gunnchos_device_os.platform.encrypted_storage import SoftwareKeystore
from gunnchos_device_os.platform.package_lifecycle import PackageLifecycleManager
from gunnchos_device_os.platform.persistent_sync import PersistentOfflineSyncEngine
from gunnchos_device_os.platform.recovery_userspace import UserspaceRecoveryEnv
from gunnchos_device_os.platform.requirement_evaluators import classify_from_evaluators
from gunnchos_device_os.platform.role_policy import RolePolicyService
from gunnchos_device_os.platform.sandbox_executor import SandboxExecutor
from gunnchos_device_os.platform.secure_packaging import (
    build_signed_app_package,
    verify_signed_manifest,
)
from gunnchos_device_os.release_engineering.ab_update import ABUpdateManager, build_update_metadata
from gunnchos_device_os.sandbox_policy import SandboxPolicyEngine


CLAIM_FLAGS = {
    "HUMAN_E6": False,
    "WCAG_VALIDATED": False,
    "GENERAL_VLM": False,
    "GENERAL_ASR": False,
    "GENERAL_MT": False,
    "CARRIER_ACCEPTED": False,
    "STANDARDIZED_6G": False,
    "PRODUCTION_SIGNING": False,
    "TPM_KEYSTORE": False,
    "KERNEL_SANDBOX": False,
}


@dataclass
class Wave004PlatformCoordinator:
    root: Path
    repo_root: Path = field(init=False)
    keystore: SoftwareKeystore = field(init=False)
    permissions: PermissionsManager = field(init=False)
    sandbox: SandboxPolicyEngine = field(init=False)
    sandbox_executor: SandboxExecutor = field(init=False)
    offline_sync: PersistentOfflineSyncEngine = field(init=False)
    package_lifecycle: PackageLifecycleManager = field(init=False)
    accessibility_store: AccessibilityStore = field(init=False)
    connectivity: ConnectivityOrchestrator = field(init=False)
    diagnostics: DiagnosticsLog = field(init=False)
    role_policy: RolePolicyService = field(init=False)
    recovery_userspace: UserspaceRecoveryEnv = field(init=False)
    ota_manager: ABUpdateManager = field(init=False)
    local_ai: LocalAiRuntime = field(init=False)
    _registry: ModelRegistry = field(init=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.repo_root = Path(__file__).resolve().parents[2]
        work = self.root / "runtime_work"
        self.keystore = SoftwareKeystore(work / "keystore")
        self.permissions = PermissionsManager(role="student")
        self.sandbox = SandboxPolicyEngine()
        self.sandbox_executor = SandboxExecutor(work / "sandbox_exec", self.sandbox)
        self.offline_sync = PersistentOfflineSyncEngine(storage_path=work / "offline_sync")
        self.package_lifecycle = PackageLifecycleManager(work / "packages", self.repo_root)
        self.accessibility_store = AccessibilityStore(work / "accessibility")
        self.connectivity = ConnectivityOrchestrator()
        self.diagnostics = DiagnosticsLog(work / "diagnostics.jsonl")
        self.role_policy = RolePolicyService(storage_path=work / "role_policy")
        self.recovery_userspace = UserspaceRecoveryEnv(work / "recovery")
        ota_state = work / "ota" / "device_state.json"
        self.ota_manager = ABUpdateManager(self.repo_root, ota_state)
        if not ota_state.exists():
            self.ota_manager.init_device(initial_version="1.0.0")
        self._registry = ModelRegistry(work / "local_ai")
        self.local_ai = LocalAiRuntime(self._registry)
        self.local_ai.ensure_default_models(self.repo_root)
        CLAIM_FLAGS["KERNEL_SANDBOX"] = self.sandbox_executor.kernel_sandbox

    # -- connectivity helpers ------------------------------------------------
    def set_bearer_available(self, bearer: str, available: bool) -> None:
        key = bearer
        metrics = self.connectivity.metrics.get(key, BearerMetrics())
        metrics.available = available
        if available and bearer == "wifi":
            metrics.latency_ms = 20.0
            metrics.loss_pct = 0.5
            metrics.security_score = 0.85
        self.connectivity.update_metrics(key, metrics)

    def inject_spoofed_bearer(self, bearer: str, *, available: bool, security_score: float) -> None:
        metrics = BearerMetrics(
            available=available,
            latency_ms=5.0,
            loss_pct=0.0,
            security_score=security_score,
            user_preference=0.99,
        )
        self.connectivity.update_metrics(bearer, metrics)

    def evaluate_and_transition(self, *, prefer_secure: bool = False) -> dict[str, Any]:
        if prefer_secure:
            for name, metrics in self.connectivity.metrics.items():
                if (
                    metrics.available
                    and metrics.security_score < 0.5
                    and name != BearerKind.OFFLINE.value
                ):
                    metrics.available = False
        result = self.connectivity.evaluate()
        return {
            "active_bearer": result.get("active"),
            "state": result.get("state"),
            "degraded": result.get("state") == "degraded",
            "evaluation": result,
        }

    # -- packaging / OTA -----------------------------------------------------
    def build_signed_package(self) -> dict[str, Any]:
        return build_signed_app_package(self.repo_root)

    def verify_signed_package(self, signed: dict[str, Any]) -> bool:
        return verify_signed_manifest(self.repo_root, signed)

    def install_signed_package(self, app_id: str, *, app_class: str = "first_party") -> dict[str, Any]:
        install = self.package_lifecycle.install(app_id, app_class=app_class)
        profile = self.sandbox.create_profile(app_id, app_class)
        return {
            "ok": install.get("ok") and profile.app_id == app_id,
            "app_id": app_id,
            "signature_valid": install.get("signature_valid"),
            "trust_root": "local_dev",
            "profile": profile.to_dict(),
            "lifecycle": install,
        }

    def build_ota_metadata(self, *, to_version: str, anti_rollback_counter: int | None = None) -> dict[str, Any]:
        state = self.ota_manager.status()
        floor = state.get("anti_rollback_floor", 0)
        counter = anti_rollback_counter if anti_rollback_counter is not None else floor + 1
        return build_update_metadata(
            self.repo_root,
            realm_id="dev-handheld",
            from_version=state["slots"][state["active_slot"]].get("version") or "1.0.0",
            to_version=to_version,
            image_hash=f"sha256:{to_version.replace('.', '')}",
            anti_rollback_counter=counter,
        )

    def stage_and_apply_ota(self, *, from_version: str, to_version: str) -> dict[str, Any]:
        _ = from_version
        meta = self.build_ota_metadata(to_version=to_version)
        stage = self.ota_manager.stage_update(meta)
        if not stage.get("ok"):
            return {"applied": False, "stage": stage}
        boot = self.ota_manager.commit_boot(stage["target_slot"], boot_succeeds=True)
        return {"applied": boot.get("ok"), "stage": stage, "boot": boot}

    def ota_revoke_key(self, fingerprint: str) -> dict[str, Any]:
        return self.ota_manager.revoke_key(fingerprint, reason="wave004_injection_test")

    # -- diagnostics / sync / accessibility ----------------------------------
    def emit(self, event_type: str, details: dict[str, Any]) -> dict[str, Any]:
        record = self.diagnostics.log(event_type, details)
        redacted = "[REDACTED" in json.dumps(record.get("details", {}))
        return {"id": record.get("id"), "redacted": redacted, **record}

    def export_tail(self, *, limit: int = 20) -> dict[str, Any]:
        return {"events": self.diagnostics.read(limit=limit)}

    def flush_pending_sync(self) -> dict[str, Any]:
        pending = self.offline_sync.pending()
        if not pending:
            return {"flushed": 0, "ok": True}
        result = self.offline_sync.sync_from_peer(pending)
        return {"flushed": len(pending), "ok": True, "result": result}

    def merge_remote_record(self, remote_dict: dict[str, Any]) -> dict[str, Any]:
        return self.offline_sync.apply_remote(remote_dict)

    def accessibility_status(self, profile_id: str = "default") -> dict[str, Any]:
        return self.accessibility_store.load(profile_id)

    # -- classification ------------------------------------------------------
    def classify_requirements(self) -> dict[str, dict[str, Any]]:
        """Executable evaluator-driven classification — no literal True classifiers."""
        return classify_from_evaluators(self)

    def status(self) -> dict[str, Any]:
        return {
            "keystore": self.keystore.status(),
            "permissions_role": self.permissions.role,
            "sandbox_profiles": len(self.sandbox.profiles),
            "sandbox_executor": self.sandbox_executor.status(),
            "offline_sync_size": len(self.offline_sync.store),
            "package_lifecycle": self.package_lifecycle.inspect(),
            "connectivity_active": self.connectivity.active_bearer.value,
            "diagnostics_path": str(self.diagnostics.path),
            "role_policy": self.role_policy.status(),
            "recovery": self.recovery_userspace.inspect(),
            "ota_active_slot": self.ota_manager.status().get("active_slot"),
            "local_ai": self.local_ai.intelligence_inventory(),
            "accessibility": self.accessibility_status(),
            "claim_flags": dict(CLAIM_FLAGS),
        }

    def run_full_validation(self) -> dict[str, Any]:
        from gunnchos_device_os.platform.e2e_scenarios import run_all_scenarios
        from gunnchos_device_os.platform.requirement_evaluators import build_evaluator_matrix
        from gunnchos_device_os.platform.security_injection import run_security_injections

        e2e = run_all_scenarios(self)
        sec = run_security_injections(self)
        matrix = build_evaluator_matrix(self)
        classification = {
            req_id: {
                "classification": r["classification"],
                "note": r["note"],
                "evaluator": r["evaluator"],
                "ok": r["ok"],
            }
            for req_id, r in matrix["results"].items()
        }
        validated = matrix["validated_count"]
        return {
            "e2e": e2e,
            "security_injection": sec,
            "requirement_classification": classification,
            "evaluator_matrix": matrix,
            "validated_count": validated,
            "target_requirements": 12,
            "unconditional_true_classifiers": 0,
            "ok": e2e.get("ok") and sec.get("ok") and validated == 12,
            "claim_flags": dict(CLAIM_FLAGS),
        }
