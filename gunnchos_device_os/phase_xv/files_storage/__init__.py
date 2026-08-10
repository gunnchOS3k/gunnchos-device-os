"""FILES_STORAGE — storage contracts, quotas, atomic write, near-full + failure E2E.

Media endurance remains PHYSICAL_PENDING. Includes Handheld 32GB headroom math
and WP-002 Outcome A (system eMMC + expansion) recalculation.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

CLAIM_BOUNDARY = (
    "Digital storage contracts/quotas/atomic writes only. "
    "Media endurance PHYSICAL_PENDING. Handheld 32GB headroom recalculated with FS overhead. "
    "WP-002 Outcome A: system-only eMMC + supported microSD expansion."
)

# GiB
HANDHELD_CAPACITY_GB = 32.0
HANDHELD_USABLE_FRACTION = 0.93

# Legacy all-onboard Phase XIV reduced profile (unsafe on 32G usable)
HANDHELD_REDUCED_PROFILE_GB = {
    "slot_a": 5.0,
    "slot_b": 5.0,
    "recovery": 2.0,
    "apps_flatpak": 4.0,
    "games_local_cache": 6.0,
    "ai_nano_fast": 4.0,
    "vision_speech": 1.0,
    "embeddings": 0.5,
    "project_indexes": 0.5,
    "update_reserve": 2.0,
    "user_reserve": 1.5,
}

OVERHEAD_GB = {
    "filesystem_overhead": 1.6,  # ~5% ext4/f2fs metadata on 32G
    "logs": 0.5,
    "update_temp": 1.0,
    "caches": 0.5,
    "system_reserves": 0.5,
}

# WP-002 Outcome A — onboard system-only placement (content, not free reserves)
OUTCOME_A_ONBOARD_GB = {
    "slot_a": 5.0,
    "slot_b": 5.0,
    "recovery": 2.0,
    "boot_firmware": 0.25,
    "gunnchos_apps_core": 2.0,
    "ai_nano_core": 2.0,
    "vision_speech_stub": 0.25,
    "embeddings_stub": 0.25,
    "logs": 0.5,
    "crash_dumps": 0.25,
    "update_temp": 1.0,
    "user_micro_workspace": 0.5,
}

OUTCOME_A_ONBOARD_RESERVES_GB = {
    "update_rollback_reserve": 2.0,
    "emergency_save_reserve": 0.5,
    "min_absolute_or_percent_free": 2.976,
    "wear_leveling_extra": 0.5,
}

OUTCOME_A_EXPANSION_GB = {
    "four_first_party_game_installs": 6.0,
    "representative_game_patches": 1.5,
    "shader_caches": 1.0,
    "flatpak_runtime_overhead": 4.0,
    "ai_fast_pro_tiers": 3.0,
    "vision_speech_full": 1.0,
    "embeddings_reranker": 0.75,
    "ai_model_update_overlap": 1.0,
    "project_indexes": 0.5,
    "waike_offline_pack": 1.5,
    "archive_playable_data": 2.0,
    "user_documents": 2.0,
    "screenshots_captures": 1.0,
    "save_data": 0.5,
    "browser_cache": 1.0,
    "messaging_media_cache": 1.0,
    "filesystem_overhead": 1.5,
}


@dataclass
class Quota:
    volume: str
    limit_bytes: int
    used_bytes: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.limit_bytes - self.used_bytes)


class StoragePlane:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.volumes = {
            "system": self.root / "system",
            "user": self.root / "user",
            "cache": self.root / "cache",
            "expansion": self.root / "expansion",
        }
        for v in self.volumes.values():
            v.mkdir(parents=True, exist_ok=True)
        self.quotas: dict[str, Quota] = {
            "user": Quota("user", limit_bytes=8 * 1024 * 1024),  # 8 MiB digital sandbox
            "cache": Quota("cache", limit_bytes=2 * 1024 * 1024),
            "expansion": Quota("expansion", limit_bytes=32 * 1024 * 1024),
        }
        self.failures: list[dict[str, Any]] = []
        self.expansion_mounted = True

    def atomic_write(self, volume: str, rel: str, data: bytes) -> dict[str, Any]:
        if volume not in self.volumes:
            raise KeyError(volume)
        if volume == "expansion" and not self.expansion_mounted:
            err = {"ok": False, "error": "volume_unmounted", "volume": volume}
            self.failures.append(err)
            return err
        q = self.quotas.get(volume)
        if q and q.used_bytes + len(data) > q.limit_bytes:
            err = {"ok": False, "error": "quota_exceeded", "volume": volume, "need": len(data), "remaining": q.remaining}
            self.failures.append(err)
            return err
        dest = self.volumes[volume] / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(dest.parent), prefix=".atomic-")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, dest)
        except Exception:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
            raise
        if q:
            q.used_bytes += len(data)
        return {"ok": True, "path": str(dest.relative_to(self.root)), "bytes": len(data), "atomic": True}

    def near_full_e2e(self) -> dict[str, Any]:
        q = self.quotas["user"]
        # Fill until near full
        chunk = b"x" * (64 * 1024)
        writes = 0
        while q.remaining >= len(chunk):
            r = self.atomic_write("user", f"fill/{writes}.bin", chunk)
            if not r["ok"]:
                break
            writes += 1
        # Next write should fail
        fail = self.atomic_write("user", "fill/overflow.bin", chunk)
        # Small write that still fits (if any remaining)
        small_ok = None
        if q.remaining > 0:
            small_ok = self.atomic_write("user", "fill/tail.bin", b"y" * min(16, q.remaining))
        return {
            "writes": writes,
            "overflow_denied": fail.get("error") == "quota_exceeded",
            "remaining": q.remaining,
            "small_tail": small_ok,
        }

    def failure_e2e(self) -> dict[str, Any]:
        before = list(self.volumes["cache"].rglob("*"))
        ok = self.atomic_write("cache", "ok.bin", b"hello-atomic")
        after = [p for p in self.volumes["cache"].rglob("*") if p.is_file()]
        leftovers = [p for p in after if p.name.startswith(".atomic-")]
        return {
            "atomic_ok": ok.get("ok") is True,
            "no_tmp_leftover": leftovers == [],
            "files": len(after),
            "before_count": len(before),
        }

    def expansion_absent_e2e(self) -> dict[str, Any]:
        self.expansion_mounted = False
        denied = self.atomic_write("expansion", "games/demo.bin", b"should-fail")
        self.expansion_mounted = True
        return {
            "denied": denied.get("error") == "volume_unmounted",
            "response": denied,
        }


def recalculate_handheld_32g_headroom(artifact_dir: Path) -> dict[str, Any]:
    """Legacy all-onboard math (still unsafe) + WP-002 Outcome A safe path."""
    profile_total = sum(HANDHELD_REDUCED_PROFILE_GB.values())
    overhead_total = sum(OVERHEAD_GB.values())
    required = profile_total + overhead_total
    capacity = HANDHELD_CAPACITY_GB
    usable = round(capacity * HANDHELD_USABLE_FRACTION, 3)
    headroom = capacity - required
    safe_legacy = headroom >= 0.5

    onboard_used = sum(OUTCOME_A_ONBOARD_GB.values())
    onboard_reserves = sum(OUTCOME_A_ONBOARD_RESERVES_GB.values())
    onboard_claimed = onboard_used + onboard_reserves
    onboard_slack = round(usable - onboard_claimed, 3)
    expansion_claimed = sum(OUTCOME_A_EXPANSION_GB.values())
    outcome_a_safe = onboard_slack >= 0 and usable >= onboard_claimed

    report = {
        "schema": "gunnchos.phase_xv.handheld_32g_headroom.v2",
        "sku": "Handheld",
        "hw_source": "Radxa RM121-D8E32 32GB eMMC (preferred)",
        "capacity_gb": capacity,
        "usable_gb": usable,
        "profile_gb": dict(HANDHELD_REDUCED_PROFILE_GB),
        "profile_total_gb": profile_total,
        "overhead_gb": dict(OVERHEAD_GB),
        "overhead_total_gb": overhead_total,
        "required_gb": required,
        "headroom_gb": round(headroom, 3),
        "safe": outcome_a_safe,  # WP-002: Outcome A is the operational policy
        "legacy_all_onboard_safe": safe_legacy,
        "mathematically_sufficient": outcome_a_safe,
        "wp002": {
            "decision_outcome": "A",
            "onboard_gb": dict(OUTCOME_A_ONBOARD_GB),
            "onboard_reserves_gb": dict(OUTCOME_A_ONBOARD_RESERVES_GB),
            "onboard_claimed_gb": round(onboard_claimed, 3),
            "onboard_slack_gb": onboard_slack,
            "expansion_gb": dict(OUTCOME_A_EXPANSION_GB),
            "expansion_claimed_gb": round(expansion_claimed, 3),
            "expansion_required": True,
            "cross_ref_hardware": (
                "gunnchos-hardware-industrial-design/"
                "npi/phase_xv/handheld_storage_headroom/"
            ),
        },
        "note": (
            "Legacy all-onboard Phase XIV/XV profile remains unsafe on 32G. "
            "WP-002 Outcome A moves games/AI Fast-Pro/WAIKE/Archive/user media to microSD "
            "and keeps eMMC system-only with explicit reserves."
        ),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "HANDHELD_32G_HEADROOM.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    # Supersede prior open defect with Outcome A closure pointer (verifier still owns V1).
    defect = {
        "schema": "gunnchos.npi_defect.v1",
        "id": "NPI_DEFECT-STORAGE-HANDHELD-32G",
        "field_kit_cross_ref": "NPI_DEFECT-HANDHELD-STORAGE-HEADROOM-001",
        "severity": "high",
        "sku": "Handheld",
        "title": "Handheld 32GB eMMC operational headroom — closed under WP-002 Outcome A (pending V1)",
        "summary": (
            f"Legacy all-onboard required {required:.2f} GiB vs capacity {capacity:.1f} GiB "
            f"(headroom {headroom:.2f} GiB). Outcome A onboard claimed {onboard_claimed:.3f} GiB "
            f"on usable {usable:.3f} GiB (slack {onboard_slack:.3f} GiB) with microSD required for MLP content."
        ),
        "status": "CLOSED_OUTCOME_A_PENDING_V1",
        "decision_outcome": "A",
        "evidence": "artifacts/phase_xv/HANDHELD_32G_HEADROOM.json",
        "follow_up": ["hardware WP-002 DRAFT PR", "independent VP-002"],
        "physical_execution_freeze": True,
        "v1_certification": "NOT_SELF_CERTIFIED",
    }
    (artifact_dir / "NPI_DEFECT-STORAGE-HANDHELD-32G.json").write_text(
        json.dumps(defect, indent=2) + "\n", encoding="utf-8"
    )
    report["npi_defect"] = "artifacts/phase_xv/NPI_DEFECT-STORAGE-HANDHELD-32G.json"
    report["field_kit_cross_ref"] = "NPI_DEFECT-HANDHELD-STORAGE-HEADROOM-001"
    return report


class FilesStorage:
    def __init__(self, root: Path):
        self.root = root
        self.plane = StoragePlane(root / "plane")

    def e2e(self, artifact_dir: Path | None = None) -> dict[str, Any]:
        art = artifact_dir or (self.root / "artifacts")
        headroom = recalculate_handheld_32g_headroom(art)
        # Contract smoke
        w = self.plane.atomic_write("user", "notes/hello.txt", b"storage-contract-v1")
        near = self.plane.near_full_e2e()
        fail = self.plane.failure_e2e()
        expansion_absent = self.plane.expansion_absent_e2e()
        ok = (
            w.get("ok") is True
            and near["overflow_denied"] is True
            and fail["atomic_ok"] is True
            and fail["no_tmp_leftover"] is True
            and expansion_absent["denied"] is True
            and "required_gb" in headroom
            and headroom["wp002"]["decision_outcome"] == "A"
            and headroom["safe"] is True
            and headroom["legacy_all_onboard_safe"] is False
        )
        return {
            "schema": "gunnchos.phase_xv.files_storage.e2e.v2",
            "ok": ok,
            "exit_state": "DIGITALLY_VALIDATED" if ok else "INCOMPLETE_DIGITAL",
            "media_endurance": "PHYSICAL_PENDING",
            "atomic_write": w,
            "near_full": near,
            "failure": fail,
            "expansion_absent": expansion_absent,
            "quotas": {k: asdict(v) for k, v in self.plane.quotas.items()},
            "handheld_32g_headroom": {
                "required_gb": headroom["required_gb"],
                "headroom_gb": headroom["headroom_gb"],
                "safe": headroom["safe"],
                "legacy_all_onboard_safe": headroom["legacy_all_onboard_safe"],
                "wp002_outcome": headroom["wp002"]["decision_outcome"],
                "onboard_slack_gb": headroom["wp002"]["onboard_slack_gb"],
                "npi_defect": headroom.get("npi_defect"),
            },
            "claim_boundary": CLAIM_BOUNDARY,
            "frontier_parity_claimed": False,
        }
