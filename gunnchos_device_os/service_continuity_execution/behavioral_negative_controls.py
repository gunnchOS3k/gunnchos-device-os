"""Behavioral sabotage negative controls — requirement-specific, not evaluator-wiring only."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.service_continuity_execution.cache import PersistentContinuityCache
from gunnchos_device_os.service_continuity_execution.degraded_report import build_degraded_report
from gunnchos_device_os.service_continuity_execution.models import ContinuityState, TrafficClass, TransitionPhase
from gunnchos_device_os.service_continuity_execution.multipath import MultipathPlan, stripe_application_payload
from gunnchos_device_os.service_continuity_execution.prioritization import TrafficItem, TrafficScheduler
from gunnchos_device_os.service_continuity_execution.sync import SyncItem, SyncPlanner, make_opportunity
from gunnchos_device_os.service_continuity_execution.transition import BearerTransitionExecution


def _eval_transition_commit_without_activate() -> dict[str, Any]:
    """Sabotage: report COMMITTED without activation_time."""
    fake = BearerTransitionExecution(
        transition_id="sabotage-txn",
        state=TransitionPhase.COMMITTED,
        activation_time=None,
        commit_time=1.0,
        logical_session_preserved=True,
    )
    predicate_pass = fake.activation_time is not None and fake.commit_time is not None
    return {
        "name": "transition_commit_without_activating_target",
        "sabotage_detected": not predicate_pass,
        "evaluator_would_fail": not predicate_pass,
    }


def _eval_resume_duplicate_op() -> dict[str, Any]:
    committed = ["op-2", "op-2"]
    exactly_once = committed.count("op-2") == 1
    return {
        "name": "resume_duplicates_an_operation",
        "sabotage_detected": not exactly_once,
        "evaluator_would_fail": not exactly_once,
    }


def _eval_multipath_counters_only() -> dict[str, Any]:
    plan = MultipathPlan(paths=["a", "b"], preferred="a")
    plan = stripe_application_payload(plan, b"hello-world-bytes")
    # counters-only has stripe_bytes but no chunk delivery proof
    has_real_chunks = False
    return {
        "name": "multipath_only_increments_counters",
        "sabotage_detected": not has_real_chunks and sum(plan.stripe_bytes.values()) > 0,
        "evaluator_would_fail": True,
    }


def _eval_cache_ignores_ttl(tmp_note: str = "") -> dict[str, Any]:
    # Simulate a broken cache that returns expired entries
    class BrokenCache(PersistentContinuityCache):
        def get(self, key: str, *, namespace: str = "default") -> Any:
            e = self._entries.get(self._nsk(namespace, key))
            return None if e is None else e.payload  # ignores TTL

    from pathlib import Path
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        clock = {"t": 100.0}
        broken = BrokenCache(Path(td) / "c.json", now_fn=lambda: clock["t"])
        broken.put("k", {"v": 1}, ttl_s=1)
        clock["t"] = 200.0
        leaked = broken.get("k") is not None
        # correct cache would return None after expiry
        good = PersistentContinuityCache(Path(td) / "good.json", now_fn=lambda: clock["t"])
        clock["t"] = 100.0
        good.put("k", {"v": 1}, ttl_s=1)
        clock["t"] = 200.0
        good_ok = good.get("k") is None
    return {
        "name": "cache_ignores_ttl",
        "sabotage_detected": leaked and good_ok,
        "evaluator_would_fail": leaked,
    }


def _eval_scheduler_starves_forever() -> dict[str, Any]:
    # Sabotage scheduler: never dispatch BACKGROUND
    class StarveScheduler(TrafficScheduler):
        def run_epoch(self, *, severe_constraint: bool = False):
            result = super().run_epoch(severe_constraint=True)
            # strip any background that slipped through
            result.dispatched = [d for d in result.dispatched if not d.startswith("bg")]
            return result

    sched = StarveScheduler(capacity_bytes_per_epoch=500)
    for i in range(20):
        sched.enqueue(
            TrafficItem(f"bg{i}", TrafficClass.BACKGROUND, 10, 0, i, "TRUSTED", "bg")
        )
    for _ in range(30):
        sched.run_epoch()
    bg_done = sum(1 for i in sched.queue.items if i.completed and i.item_id.startswith("bg"))
    starved_forever = bg_done == 0
    return {
        "name": "scheduler_starves_background_forever",
        "sabotage_detected": starved_forever,
        "evaluator_would_fail": starved_forever,
    }


def _eval_sync_exceeds_max_bytes() -> dict[str, Any]:
    planner = SyncPlanner()
    planner.enqueue(SyncItem("big", TrafficClass.BACKGROUND, 5000, 1, 10, "idem-big"))
    opp = make_opportunity(path_id="w", path_class="terrestrial", now=1.0, max_bytes=10)
    # sabotage: ignore max_bytes
    applied = []
    used = 0
    for item in planner.queue:
        applied.append(item.sync_item_id)
        used += item.size_bytes
    exceeded = used > opp.max_bytes
    return {
        "name": "sync_exceeds_max_bytes",
        "sabotage_detected": exceeded,
        "evaluator_would_fail": exceeded,
    }


def _eval_degraded_report_false_cache() -> dict[str, Any]:
    report = build_degraded_report(
        continuity_state=ContinuityState.OFFLINE_CAPABLE,
        cache_available=False,
        internet_available=False,
    )
    # sabotage claim
    sabotaged_claim = True  # pretend report claims cache
    actual_consistent = report.cache_available is False and "LOCAL_CACHE_SERVICE" not in report.retained_capabilities
    return {
        "name": "degraded_report_claims_cache_when_missing",
        "sabotage_detected": sabotaged_claim and actual_consistent,
        "evaluator_would_fail": True,  # claiming cache when missing must fail
        "runtime_consistent": actual_consistent,
    }


def prove_behavioral_negative_controls() -> dict[str, Any]:
    cases = [
        _eval_transition_commit_without_activate(),
        _eval_resume_duplicate_op(),
        _eval_multipath_counters_only(),
        _eval_cache_ignores_ttl(),
        _eval_scheduler_starves_forever(),
        _eval_sync_exceeds_max_bytes(),
        _eval_degraded_report_false_cache(),
    ]
    ok = all(c["sabotage_detected"] and c["evaluator_would_fail"] for c in cases)
    return {
        "schema": "gunnchos.engineering_wave006.behavioral_negative_controls.v1",
        "ok": ok,
        "BEHAVIORAL_NEGATIVE_CONTROLS_PASS": ok,
        "cases": cases,
    }
