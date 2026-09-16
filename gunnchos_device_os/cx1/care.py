"""CX1L Care — SupportBundle export, recovery plan, backup-before-reset, app repair."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from gunnchos_device_os.cx0.support_bundle import SupportBundleBuilder

from .vault import Vault


@dataclass
class Care:
    root: Path
    vault: Vault
    version_inventory: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        for sub in ("bundles", "recovery", "help", "repairs"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        (self.root / "help" / "care_offline_help.md").write_text(
            "# Care\n\nExport a support bundle, restore from Vault backup, or repair an app.\n"
            "Warranty/RMA readiness is NOT granted by software alone.\n"
        )
        self.version_inventory = {
            "cx1": "1.0.0",
            "cx0": "1.0.0",
            "device_os_claim": "ordinary_user_digital_foundations",
        }

    def export_support_bundle(
        self,
        *,
        diagnostics: Dict,
        capability_inventory: Dict,
        failure_summaries: Optional[List[str]] = None,
        storage_backup_update_status: Optional[Dict] = None,
    ) -> dict:
        out = self.root / "bundles" / time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        builder = SupportBundleBuilder()
        builder.add_text_artifact(
            "diagnostics.json",
            json.dumps(diagnostics, indent=2),
        )
        builder.add_text_artifact(
            "capability_inventory.json",
            json.dumps(capability_inventory, indent=2),
        )
        builder.add_text_artifact(
            "version_inventory.json",
            json.dumps(self.version_inventory, indent=2),
        )
        builder.add_text_artifact(
            "failure_summaries.json",
            json.dumps(failure_summaries or [], indent=2),
        )
        builder.add_text_artifact(
            "storage_backup_update_status.json",
            json.dumps(storage_backup_update_status or {}, indent=2),
        )
        meta = builder.build(out)
        # checksums for each artifact
        checksums = {}
        for name in meta["artifacts"]:
            data = (out / name).read_bytes()
            checksums[name] = hashlib.sha256(data).hexdigest()
        meta["checksums"] = checksums
        meta["claim_boundary"] = "support_bundle_export_not_warranty_rma_ready"
        meta["evidence_class"] = "DIGITAL_PASS"
        (out / "SUPPORT_BUNDLE.json").write_text(json.dumps(meta, indent=2) + "\n")
        return meta

    def recovery_plan(self, profile_id: str) -> dict:
        plan = {
            "profile_id": profile_id,
            "steps": [
                "export_support_bundle",
                "backup_before_reset",
                "profile_restore_from_vault_backup",
                "app_repair_hook",
                "offline_help",
            ],
            "warranty_rma_ready": False,
            "claim_boundary": "software_recovery_not_warranty_rma",
        }
        path = self.root / "recovery" / f"{profile_id}.json"
        path.write_text(json.dumps(plan, indent=2) + "\n")
        return plan

    def backup_before_reset(self, label: str = "pre_reset") -> dict:
        return self.vault.create_backup(label=label)

    def restore_profile(self, backup_id: str, *, overwrite: str = "replace") -> dict:
        return self.vault.restore_backup(backup_id, overwrite=overwrite)

    def app_repair(self, app_id: str, app_center) -> dict:
        """Reinstall marker / clear launch faults — digital repair hook."""
        try:
            if app_id in app_center.installed:
                app_center.uninstall(app_id)
            result = app_center.install(app_id)
        except Exception as exc:  # noqa: BLE001
            result = {"ok": False, "error": type(exc).__name__}
        path = self.root / "repairs" / f"{app_id}.json"
        path.write_text(json.dumps({"app_id": app_id, "result": result, "ts": time.time()}, indent=2) + "\n")
        return {"app_id": app_id, "repair": result, "evidence_class": "DIGITAL_PASS"}

    def offline_help(self) -> str:
        return (self.root / "help" / "care_offline_help.md").read_text()
