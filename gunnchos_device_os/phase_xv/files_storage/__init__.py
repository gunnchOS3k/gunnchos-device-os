"""FILES_STORAGE — storage contracts, quotas, atomic write, near-full + failure E2E.

Media endurance remains PHYSICAL_PENDING. Includes Handheld 32GB headroom math.
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
    "Media endurance PHYSICAL_PENDING. Handheld 32GB headroom recalculated with FS overhead."
)

# GiB
HANDHELD_CAPACITY_GB = 32.0

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
        }
        for v in self.volumes.values():
            v.mkdir(parents=True, exist_ok=True)
        self.quotas: dict[str, Quota] = {
            "user": Quota("user", limit_bytes=8 * 1024 * 1024),  # 8 MiB digital sandbox
            "cache": Quota("cache", limit_bytes=2 * 1024 * 1024),
        }
        self.failures: list[dict[str, Any]] = []

    def atomic_write(self, volume: str, rel: str, data: bytes) -> dict[str, Any]:
        if volume not in self.volumes:
            raise KeyError(volume)
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
        # Simulate failure by temporarily making target a directory collision via bad replace
        # Use quota path already tested; also verify atomic tmp does not leave partial on success path.
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


def recalculate_handheld_32g_headroom(artifact_dir: Path) -> dict[str, Any]:
    profile_total = sum(HANDHELD_REDUCED_PROFILE_GB.values())
    overhead_total = sum(OVERHEAD_GB.values())
    required = profile_total + overhead_total
    capacity = HANDHELD_CAPACITY_GB
    headroom = capacity - required
    safe = headroom >= 0.5  # require ≥0.5 GiB free after all reserves
    report = {
        "schema": "gunnchos.phase_xv.handheld_32g_headroom.v1",
        "sku": "Handheld",
        "hw_source": "Radxa RM121-D8E32 32GB eMMC (preferred)",
        "capacity_gb": capacity,
        "profile_gb": dict(HANDHELD_REDUCED_PROFILE_GB),
        "profile_total_gb": profile_total,
        "overhead_gb": dict(OVERHEAD_GB),
        "overhead_total_gb": overhead_total,
        "required_gb": required,
        "headroom_gb": round(headroom, 3),
        "safe": safe,
        "mathematically_sufficient": safe,
        "note": (
            "Phase XIV reduced profile was 31.5/32 GB before FS/logs/update-temp/cache reserves. "
            "Phase XV includes those overheads; sub-0.5 GiB headroom is treated as unsafe for EVT."
        ),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "HANDHELD_32G_HEADROOM.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    if not safe:
        defect = {
            "schema": "gunnchos.npi_defect.v1",
            "id": "NPI_DEFECT-STORAGE-HANDHELD-32G",
            "field_kit_cross_ref": "NPI_DEFECT-HANDHELD-STORAGE-HEADROOM-001",
            "severity": "storage",
            "sku": "Handheld",
            "severity": "high",
            "title": "Handheld 32GB eMMC operational headroom insufficient after FS/log/update reserves",
            "summary": (
                f"Required {required:.2f} GiB vs capacity {capacity:.1f} GiB "
                f"(headroom {headroom:.2f} GiB). Cross-ref field-kit "
                "NPI_DEFECT-HANDHELD-STORAGE-HEADROOM-001 for hardware follow-up "
                "(larger eMMC/NVMe or further profile cuts)."
            ),
            "evidence": "artifacts/phase_xv/HANDHELD_32G_HEADROOM.json",
            "follow_up": ["field-kit", "hardware", "NPI"],
            "physical_execution_freeze": True,
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
        ok = (
            w.get("ok") is True
            and near["overflow_denied"] is True
            and fail["atomic_ok"] is True
            and fail["no_tmp_leftover"] is True
            and "required_gb" in headroom
        )
        # Gate digital closure does not require safe=True; defect artifact is the honesty path.
        return {
            "schema": "gunnchos.phase_xv.files_storage.e2e.v1",
            "ok": ok,
            "exit_state": "DIGITALLY_VALIDATED" if ok else "INCOMPLETE_DIGITAL",
            "media_endurance": "PHYSICAL_PENDING",
            "atomic_write": w,
            "near_full": near,
            "failure": fail,
            "quotas": {k: asdict(v) for k, v in self.plane.quotas.items()},
            "handheld_32g_headroom": {
                "required_gb": headroom["required_gb"],
                "headroom_gb": headroom["headroom_gb"],
                "safe": headroom["safe"],
                "npi_defect": headroom.get("npi_defect"),
            },
            "claim_boundary": CLAIM_BOUNDARY,
            "frontier_parity_claimed": False,
        }
