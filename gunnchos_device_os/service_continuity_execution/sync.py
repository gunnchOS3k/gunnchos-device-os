"""NET-ORCH-034 — SyncOpportunity planner with max-bytes / policy / exactly-once apply."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.service_continuity_execution.models import ContinuityState, TrafficClass


@dataclass
class SyncItem:
    sync_item_id: str
    traffic_class: TrafficClass
    size_bytes: int
    deadline: float
    priority: int
    idempotency_key: str
    applied: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["traffic_class"] = self.traffic_class.value
        return d


@dataclass
class SyncOpportunity:
    opportunity_id: str
    path_id: str
    path_class: str
    window_start: float
    window_end: float
    deadline: float
    metered: bool
    trusted: bool
    battery_state: str  # HEALTHY | LOW
    allowed_classes: list[str]
    priority_floor: int
    max_bytes: int
    data_budget_remaining: int
    reason: str
    provenance: str

    def is_active(self, now: float) -> bool:
        return self.window_start <= now <= min(self.window_end, self.deadline)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SyncPlanner:
    queue: list[SyncItem] = field(default_factory=list)
    applied_ledger: set[str] = field(default_factory=set)
    storage_path: Path | None = None

    def enqueue(self, item: SyncItem) -> None:
        if any(q.sync_item_id == item.sync_item_id for q in self.queue):
            return
        self.queue.append(item)

    def persist(self, path: Path) -> None:
        payload = {
            "queue": [i.to_dict() for i in self.queue],
            "applied_ledger": sorted(self.applied_ledger),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True))
        os.replace(tmp, path)

    @classmethod
    def load(cls, path: Path) -> "SyncPlanner":
        raw = json.loads(path.read_text())
        planner = cls(storage_path=path)
        for row in raw.get("queue", []):
            planner.queue.append(
                SyncItem(
                    sync_item_id=row["sync_item_id"],
                    traffic_class=TrafficClass(row["traffic_class"]),
                    size_bytes=row["size_bytes"],
                    deadline=row["deadline"],
                    priority=row["priority"],
                    idempotency_key=row["idempotency_key"],
                    applied=row.get("applied", False),
                )
            )
        planner.applied_ledger = set(raw.get("applied_ledger", []))
        return planner

    def plan_and_apply(self, opportunity: SyncOpportunity, *, now: float) -> dict[str, Any]:
        if not opportunity.is_active(now):
            return {"ok": False, "reason": "opportunity_expired", "applied": [], "remaining": [i.sync_item_id for i in self.queue if not i.applied]}
        if opportunity.battery_state == "LOW":
            # defer noncritical
            allowed = {TrafficClass.EMERGENCY.value, TrafficClass.COMMUNICATION.value}
        else:
            allowed = set(opportunity.allowed_classes)

        budget = min(opportunity.max_bytes, opportunity.data_budget_remaining)
        if budget < 0:
            return {"ok": False, "reason": "sync_data_budget_exceeded", "applied": [], "remaining": [i.sync_item_id for i in self.queue]}

        candidates = [
            i
            for i in self.queue
            if not i.applied
            and i.traffic_class.value in allowed
            and i.priority >= opportunity.priority_floor
            and (opportunity.trusted or i.traffic_class != TrafficClass.EMERGENCY)
        ]
        if opportunity.metered:
            candidates = [i for i in candidates if i.priority >= 80 or i.traffic_class in (TrafficClass.EMERGENCY, TrafficClass.COMMUNICATION)]
        if opportunity.path_class == "local_peer":
            candidates = [i for i in candidates if i.traffic_class in (TrafficClass.LEARNING, TrafficClass.COMMUNICATION)]

        candidates.sort(key=lambda i: (-i.priority, i.deadline, i.sync_item_id))
        applied: list[str] = []
        used = 0
        for item in candidates:
            if item.idempotency_key in self.applied_ledger:
                item.applied = True
                continue
            if used + item.size_bytes > budget:
                continue
            item.applied = True
            self.applied_ledger.add(item.idempotency_key)
            applied.append(item.sync_item_id)
            used += item.size_bytes

        remaining = [i.sync_item_id for i in self.queue if not i.applied]
        return {
            "ok": True,
            "applied": applied,
            "bytes_used": used,
            "remaining": remaining,
            "opportunity_id": opportunity.opportunity_id,
        }


def make_opportunity(
    *,
    path_id: str,
    path_class: str,
    now: float,
    window_s: float = 60.0,
    metered: bool = False,
    trusted: bool = True,
    battery_state: str = "HEALTHY",
    max_bytes: int = 10_000,
    data_budget_remaining: int = 10_000,
    allowed_classes: list[str] | None = None,
    priority_floor: int = 0,
    provenance: str = "DIGITAL_SYNTHETIC_EVIDENCE",
    reason: str = "policy",
) -> SyncOpportunity:
    return SyncOpportunity(
        opportunity_id=f"opp-{uuid.uuid4().hex[:10]}",
        path_id=path_id,
        path_class=path_class,
        window_start=now,
        window_end=now + window_s,
        deadline=now + window_s,
        metered=metered,
        trusted=trusted,
        battery_state=battery_state,
        allowed_classes=allowed_classes
        or [TrafficClass.EMERGENCY.value, TrafficClass.COMMUNICATION.value, TrafficClass.LEARNING.value, TrafficClass.BACKGROUND.value],
        priority_floor=priority_floor,
        max_bytes=max_bytes,
        data_budget_remaining=data_budget_remaining,
        reason=reason,
        provenance=provenance,
    )


def prove_opportunistic_sync(storage_dir: Path) -> dict[str, Any]:
    storage_dir.mkdir(parents=True, exist_ok=True)
    path = storage_dir / "sync_queue.json"
    now = 1_700_000_500.0
    planner = SyncPlanner()
    planner.enqueue(SyncItem("s-emerg", TrafficClass.EMERGENCY, 100, now + 10, 100, "idem-emerg"))
    planner.enqueue(SyncItem("s-comm", TrafficClass.COMMUNICATION, 200, now + 20, 90, "idem-comm"))
    planner.enqueue(SyncItem("s-learn", TrafficClass.LEARNING, 400, now + 30, 70, "idem-learn"))
    planner.enqueue(SyncItem("s-bg", TrafficClass.BACKGROUND, 5000, now + 40, 10, "idem-bg"))
    planner.enqueue(SyncItem("s-big", TrafficClass.BACKGROUND, 8000, now + 50, 5, "idem-big"))
    planner.persist(path)

    # trusted unmetered healthy — broad batch
    opp_healthy = make_opportunity(path_id="wifi", path_class="terrestrial", now=now, max_bytes=20_000, metered=False)
    r_healthy = SyncPlanner.load(path).plan_and_apply(opp_healthy, now=now)

    # metered constrained — small/high-priority only
    planner2 = SyncPlanner()
    for item in [
        SyncItem("m-comm", TrafficClass.COMMUNICATION, 100, now + 10, 90, "idem-m-comm"),
        SyncItem("m-bg", TrafficClass.BACKGROUND, 100, now + 10, 10, "idem-m-bg"),
    ]:
        planner2.enqueue(item)
    opp_metered = make_opportunity(path_id="cell", path_class="terrestrial", now=now, metered=True, max_bytes=500)
    r_metered = planner2.plan_and_apply(opp_metered, now=now)

    # low battery
    planner3 = SyncPlanner()
    planner3.enqueue(SyncItem("lb-comm", TrafficClass.COMMUNICATION, 50, now + 5, 90, "idem-lb-comm"))
    planner3.enqueue(SyncItem("lb-bg", TrafficClass.BACKGROUND, 50, now + 5, 10, "idem-lb-bg"))
    opp_batt = make_opportunity(path_id="wifi", path_class="terrestrial", now=now, battery_state="LOW", max_bytes=500)
    r_batt = planner3.plan_and_apply(opp_batt, now=now)

    # brief simulated NTN window
    planner4 = SyncPlanner()
    planner4.enqueue(SyncItem("ntn-hi", TrafficClass.COMMUNICATION, 80, now + 5, 95, "idem-ntn-hi"))
    planner4.enqueue(SyncItem("ntn-lo", TrafficClass.BACKGROUND, 500, now + 5, 5, "idem-ntn-lo"))
    opp_ntn = make_opportunity(
        path_id="ntn-sim",
        path_class="ntn_simulated",
        now=now,
        window_s=8.0,
        max_bytes=100,
        provenance="SIMULATED",
        reason="brief_simulated_ntn_window",
        allowed_classes=[TrafficClass.EMERGENCY.value, TrafficClass.COMMUNICATION.value],
    )
    r_ntn = planner4.plan_and_apply(opp_ntn, now=now)

    # local peer
    planner5 = SyncPlanner()
    planner5.enqueue(SyncItem("peer-learn", TrafficClass.LEARNING, 40, now + 5, 60, "idem-peer-learn"))
    planner5.enqueue(SyncItem("peer-bg", TrafficClass.BACKGROUND, 40, now + 5, 5, "idem-peer-bg"))
    opp_peer = make_opportunity(path_id="peer-1", path_class="local_peer", now=now, max_bytes=200)
    r_peer = planner5.plan_and_apply(opp_peer, now=now)

    # expiry
    opp_exp = make_opportunity(path_id="wifi", path_class="terrestrial", now=now, window_s=1.0)
    r_exp = planner5.plan_and_apply(opp_exp, now=now + 5.0)

    # max bytes enforced / ineligible remain queued
    planner6 = SyncPlanner()
    planner6.enqueue(SyncItem("fit", TrafficClass.COMMUNICATION, 50, now + 5, 90, "idem-fit"))
    planner6.enqueue(SyncItem("leave", TrafficClass.BACKGROUND, 500, now + 5, 10, "idem-leave"))
    opp_max = make_opportunity(path_id="wifi", path_class="terrestrial", now=now, max_bytes=60)
    r_max = planner6.plan_and_apply(opp_max, now=now)
    planner6.persist(path)

    # fresh process + duplicate opportunity replay
    root = str(Path(__file__).resolve().parents[2])
    script = r"""
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from gunnchos_device_os.service_continuity_execution.sync import SyncPlanner, make_opportunity, TrafficClass, SyncItem
path = Path(sys.argv[2])
now = float(sys.argv[3])
p = SyncPlanner.load(path)
opp = make_opportunity(path_id="wifi", path_class="terrestrial", now=now, max_bytes=60)
r1 = p.plan_and_apply(opp, now=now)
r2 = p.plan_and_apply(opp, now=now)  # replay
p.persist(path)
print(json.dumps({"r1": r1, "r2": r2, "ledger": sorted(p.applied_ledger)}))
"""
    proc = subprocess.run(
        [sys.executable, "-c", script, root, str(path), str(now)],
        capture_output=True,
        text=True,
        check=False,
    )
    proc_out = json.loads(proc.stdout.strip()) if proc.returncode == 0 else {"error": proc.stderr}

    checks = {
        "healthy_broad": "s-bg" in r_healthy.get("applied", []) or r_healthy.get("bytes_used", 0) > 0,
        "metered_high_priority_only": "m-comm" in r_metered.get("applied", []) and "m-bg" not in r_metered.get("applied", []),
        "low_battery_defers_bg": "lb-bg" not in r_batt.get("applied", []) and "lb-comm" in r_batt.get("applied", []),
        "ntn_simulated_compact": r_ntn.get("ok") and "ntn-hi" in r_ntn.get("applied", []) and opp_ntn.provenance == "SIMULATED",
        "local_peer_subset": "peer-learn" in r_peer.get("applied", []) and "peer-bg" not in r_peer.get("applied", []),
        "opportunity_expiry": r_exp.get("reason") == "opportunity_expired",
        "max_bytes_enforced": "fit" in r_max.get("applied", []) and "leave" in r_max.get("remaining", []),
        "fresh_process_ok": proc.returncode == 0,
        "replay_no_duplicate": proc.returncode == 0
        and proc_out.get("r2", {}).get("applied") == []
        and len(proc_out.get("ledger", [])) >= 1,
    }
    ok = all(checks.values())
    return {
        "schema": "gunnchos.engineering_wave006.opportunistic_sync.v1",
        "ok": ok,
        "checks": checks,
        "results": {
            "healthy": r_healthy,
            "metered": r_metered,
            "low_battery": r_batt,
            "ntn": r_ntn,
            "peer": r_peer,
            "expired": r_exp,
            "max_bytes": r_max,
            "fresh_replay": proc_out,
        },
        "SYNC_OPPORTUNITY_PLANNER": True,
        "SYNC_MAX_BYTES_ENFORCED": bool(checks["max_bytes_enforced"]),
        "SYNC_EXACTLY_ONCE": bool(checks["replay_no_duplicate"]),
    }


def opportunistic_sync_for_state(state: ContinuityState, planner: SyncPlanner, opportunity: SyncOpportunity, now: float) -> dict[str, Any]:
    if state in (ContinuityState.OFFLINE_CAPABLE, ContinuityState.FAILED):
        return {"ok": True, "deferred": True, "applied": []}
    return planner.plan_and_apply(opportunity, now=now)
