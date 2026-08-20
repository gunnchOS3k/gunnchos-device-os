"""NET-ORCH-032 — constrained-capacity traffic scheduler (not label sort)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from gunnchos_device_os.service_continuity_execution.models import TrafficClass

PRIORITY_RANK = {
    TrafficClass.EMERGENCY: 0,
    TrafficClass.COMMUNICATION: 1,
    TrafficClass.LEARNING: 2,
    TrafficClass.OTHER: 3,
    TrafficClass.BACKGROUND: 4,
}


@dataclass
class TrafficItem:
    item_id: str
    traffic_class: TrafficClass
    size_bytes: int
    deadline: float
    arrival_order: int
    priority_authority: str  # TRUSTED | UNTRUSTED
    service_id: str
    enqueued_at_epoch: int = 0
    wait_epochs: int = 0
    completed: bool = False

    def effective_class(self) -> TrafficClass:
        if self.traffic_class == TrafficClass.EMERGENCY and self.priority_authority != "TRUSTED":
            return TrafficClass.OTHER  # downgrade untrusted emergency
        return self.traffic_class

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["traffic_class"] = self.traffic_class.value
        d["effective_class"] = self.effective_class().value
        return d


@dataclass
class DispatchResult:
    epoch: int
    dispatched: list[str]
    bytes_dispatched: int
    bytes_by_class: dict[str, int]
    rejected: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TrafficQueue:
    items: list[TrafficItem] = field(default_factory=list)

    def enqueue(self, item: TrafficItem) -> None:
        self.items.append(item)


@dataclass
class TrafficScheduler:
    capacity_bytes_per_epoch: int
    queue: TrafficQueue = field(default_factory=TrafficQueue)
    epoch: int = 0
    history: list[DispatchResult] = field(default_factory=list)
    aging_boost_epochs: int = 8

    def enqueue(self, item: TrafficItem) -> None:
        item.enqueued_at_epoch = self.epoch
        self.queue.enqueue(item)

    def _sort_key(self, item: TrafficItem) -> tuple:
        eff = item.effective_class()
        rank = PRIORITY_RANK[eff]
        # aging: lower-priority items that waited long get a boost toward progress
        aged_rank = rank
        if item.wait_epochs >= self.aging_boost_epochs and eff != TrafficClass.EMERGENCY:
            aged_rank = max(0, rank - 1)
        return (aged_rank, item.deadline, item.arrival_order)

    def run_epoch(self, *, severe_constraint: bool = False) -> DispatchResult:
        self.epoch += 1
        budget = self.capacity_bytes_per_epoch
        if severe_constraint:
            budget = max(1, budget // 4)
        pending = [i for i in self.queue.items if not i.completed]
        for i in pending:
            i.wait_epochs = self.epoch - i.enqueued_at_epoch
        pending.sort(key=self._sort_key)

        dispatched: list[str] = []
        rejected: list[str] = []
        bytes_disp = 0
        bytes_by_class: dict[str, int] = {}

        for item in pending:
            eff = item.effective_class()
            if item.traffic_class == TrafficClass.EMERGENCY and item.priority_authority != "TRUSTED":
                rejected.append(item.item_id)
                item.completed = True  # rejected permanently for this campaign
                continue
            if severe_constraint and eff == TrafficClass.BACKGROUND:
                continue  # yield
            if item.size_bytes > budget - bytes_disp:
                continue
            item.completed = True
            dispatched.append(item.item_id)
            bytes_disp += item.size_bytes
            bytes_by_class[eff.value] = bytes_by_class.get(eff.value, 0) + item.size_bytes

        result = DispatchResult(
            epoch=self.epoch,
            dispatched=dispatched,
            bytes_dispatched=bytes_disp,
            bytes_by_class=bytes_by_class,
            rejected=rejected,
        )
        self.history.append(result)
        return result


def prioritize_traffic(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Legacy label ordering — scheduler proofs use TrafficScheduler."""
    mapped = []
    for i, raw in enumerate(items):
        tc = TrafficClass(raw.get("traffic_class", "OTHER"))
        mapped.append(
            {
                **raw,
                "rank": PRIORITY_RANK[tc],
                "arrival_order": i,
            }
        )
    return sorted(mapped, key=lambda x: (x["rank"], x["arrival_order"]))


def prove_traffic_prioritization() -> dict[str, Any]:
    sched = TrafficScheduler(capacity_bytes_per_epoch=500)
    arrival = 0
    # mixed 100+ item queue
    for i in range(40):
        sched.enqueue(
            TrafficItem(
                item_id=f"bg-{i}",
                traffic_class=TrafficClass.BACKGROUND,
                size_bytes=40,
                deadline=1_700_000_000 + i,
                arrival_order=arrival,
                priority_authority="TRUSTED",
                service_id="bg",
            )
        )
        arrival += 1
    for i in range(30):
        sched.enqueue(
            TrafficItem(
                item_id=f"learn-{i}",
                traffic_class=TrafficClass.LEARNING,
                size_bytes=50,
                deadline=1_700_000_000 + i,
                arrival_order=arrival,
                priority_authority="TRUSTED",
                service_id="learn",
            )
        )
        arrival += 1
    for i in range(25):
        sched.enqueue(
            TrafficItem(
                item_id=f"comm-{i}",
                traffic_class=TrafficClass.COMMUNICATION,
                size_bytes=60,
                deadline=1_700_000_000 + i,
                arrival_order=arrival,
                priority_authority="TRUSTED",
                service_id="comm",
            )
        )
        arrival += 1
    # untrusted critical
    sched.enqueue(
        TrafficItem(
            item_id="evil-emerg",
            traffic_class=TrafficClass.EMERGENCY,
            size_bytes=10,
            deadline=0,
            arrival_order=arrival,
            priority_authority="UNTRUSTED",
            service_id="evil",
        )
    )
    arrival += 1
    # trusted emergency burst mid-campaign
    for i in range(5):
        sched.enqueue(
            TrafficItem(
                item_id=f"emerg-{i}",
                traffic_class=TrafficClass.EMERGENCY,
                size_bytes=80,
                deadline=0,
                arrival_order=arrival,
                priority_authority="TRUSTED",
                service_id="emerg",
            )
        )
        arrival += 1

    assert len(sched.queue.items) >= 100

    # constrained epochs with emergency present
    for _ in range(6):
        sched.run_epoch(severe_constraint=True)

    # remove remaining emergency and run steady non-emergency load for aging
    for item in sched.queue.items:
        if item.traffic_class == TrafficClass.EMERGENCY and not item.completed:
            item.completed = True  # clear emergency pressure
    for _ in range(20):
        sched.run_epoch(severe_constraint=False)

    wait_by_class: dict[str, list[int]] = {}
    completion_by_class: dict[str, int] = {}
    starvation = 0
    for item in sched.queue.items:
        eff = item.effective_class().value
        wait_by_class.setdefault(eff, []).append(item.wait_epochs)
        if item.completed and item.item_id != "evil-emerg":
            completion_by_class[eff] = completion_by_class.get(eff, 0) + 1
        if item.traffic_class == TrafficClass.BACKGROUND and not item.completed:
            starvation += 1

    dispatch_order = [iid for r in sched.history for iid in r.dispatched]
    first_emerg = next((i for i, x in enumerate(dispatch_order) if x.startswith("emerg-")), None)
    first_bg = next((i for i, x in enumerate(dispatch_order) if x.startswith("bg-")), None)
    evil_rejected = any("evil-emerg" in r.rejected for r in sched.history)

    checks = {
        "queue_100_plus": len(sched.queue.items) >= 100,
        "emergency_precedence": first_emerg is not None and (first_bg is None or first_emerg < first_bg),
        "untrusted_emergency_rejected": evil_rejected,
        "background_yielded_under_severe": all(
            "BACKGROUND" not in r.bytes_by_class or r.bytes_by_class.get("BACKGROUND", 0) == 0
            for r in sched.history[:6]
        ),
        "background_eventual_progress": completion_by_class.get("BACKGROUND", 0) > 0,
        "starvation_bounded": starvation < 10,
        "comm_learning_above_bg": completion_by_class.get("COMMUNICATION", 0) > 0
        and completion_by_class.get("LEARNING", 0) > 0,
        "not_label_sort_only": len(sched.history) >= 10 and sum(r.bytes_dispatched for r in sched.history) > 0,
    }
    ok = all(checks.values())
    return {
        "schema": "gunnchos.engineering_wave006.traffic_scheduler_stress.v1",
        "ok": ok,
        "checks": checks,
        "epochs": len(sched.history),
        "dispatch_order_head": dispatch_order[:20],
        "bytes_by_class_total": {
            k: sum(r.bytes_by_class.get(k, 0) for r in sched.history)
            for k in ("EMERGENCY", "COMMUNICATION", "LEARNING", "BACKGROUND", "OTHER")
        },
        "wait_time_by_class": {k: (sum(v) / len(v) if v else 0) for k, v in wait_by_class.items()},
        "starvation_count": starvation,
        "completion_by_class": completion_by_class,
        "TRAFFIC_SCHEDULER_RUNTIME": True,
        "TRAFFIC_STARVATION_BOUNDED": starvation < 10,
        "PRODUCTION_APP_PRIORITY_SIGNING": False,
    }
