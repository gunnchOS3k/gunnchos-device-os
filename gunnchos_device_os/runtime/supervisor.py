"""Runtime supervisor — dependency-ordered start/stop with fault restart."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import tempfile

from gunnchos_device_os.runtime.adapters import SERVICE_CLASSES, build_service
from gunnchos_device_os.runtime.catalog import REQUIRED_SERVICE_IDS, service_matrix
from gunnchos_device_os.runtime.service_base import (
    CLAIM_BOUNDARY,
    RuntimeService,
    ServiceConfig,
    ServiceState,
)


class RuntimeSupervisor:
    """In-process digital supervisor for the gunnchOS service matrix."""

    def __init__(
        self,
        *,
        persistence_root: str | Path | None = None,
        enabled: list[str] | None = None,
    ) -> None:
        self.persistence_root = Path(
            persistence_root
            if persistence_root is not None
            else Path(tempfile.gettempdir()) / "gunnchos-runtime"
        )
        self.persistence_root.mkdir(parents=True, exist_ok=True)
        self.enabled = list(enabled or REQUIRED_SERVICE_IDS)
        self.services: dict[str, RuntimeService] = {}
        self.start_order: list[str] = []
        self.events: list[dict[str, Any]] = []

    def _topo_sort(self) -> list[str]:
        pending = {sid for sid in self.enabled if sid in SERVICE_CLASSES}
        ordered: list[str] = []
        visiting: set[str] = set()

        def visit(sid: str) -> None:
            if sid in ordered:
                return
            if sid in visiting:
                raise RuntimeError(f"dependency cycle involving {sid}")
            visiting.add(sid)
            cls = SERVICE_CLASSES[sid]
            for dep in cls.dependencies:
                if dep not in SERVICE_CLASSES:
                    raise KeyError(f"unknown dependency {dep} for {sid}")
                if dep in pending or dep in self.enabled:
                    visit(dep)
            visiting.remove(sid)
            if sid not in ordered:
                ordered.append(sid)

        for sid in sorted(pending):
            visit(sid)
        return ordered

    def _config_for(self, service_id: str) -> ServiceConfig:
        return ServiceConfig(
            service_id=service_id,
            persistence_path=str(self.persistence_root / f"{service_id}.json"),
            options={},
        )

    def start_all(self) -> dict[str, Any]:
        order = self._topo_sort()
        self.start_order = order
        statuses = []
        for sid in order:
            svc = build_service(sid, self._config_for(sid))
            status = svc.start()
            self.services[sid] = svc
            self.events.append({"event": "start", "service_id": sid, "state": status.state.value})
            if status.state == ServiceState.FAULTED and svc.config.restart_on_fault:
                svc.restart_count += 1
                status = svc.start()
                self.events.append(
                    {
                        "event": "restart",
                        "service_id": sid,
                        "state": status.state.value,
                        "restart_count": svc.restart_count,
                    }
                )
            statuses.append(status.to_dict())
        return {
            "started": [s["service_id"] for s in statuses if s["state"] == ServiceState.RUNNING.value],
            "faulted": [s["service_id"] for s in statuses if s["state"] == ServiceState.FAULTED.value],
            "order": order,
            "statuses": statuses,
            "claim_boundary": CLAIM_BOUNDARY,
            "full_operational_product_claimed": False,
        }

    def stop_all(self) -> dict[str, Any]:
        stopped = []
        for sid in reversed(self.start_order or list(self.services.keys())):
            svc = self.services.get(sid)
            if not svc:
                continue
            status = svc.stop()
            stopped.append(status.to_dict())
            self.events.append({"event": "stop", "service_id": sid})
        return {"stopped": [s["service_id"] for s in stopped], "statuses": stopped}

    def status_all(self) -> dict[str, Any]:
        return {
            "services": {sid: svc.status().to_dict() for sid, svc in self.services.items()},
            "order": list(self.start_order),
            "events": list(self.events),
            "matrix": service_matrix(),
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def call(self, service_id: str, method: str, **kwargs: Any) -> Any:
        svc = self.services.get(service_id)
        if svc is None:
            raise KeyError(f"service not started: {service_id}")
        return svc.api(method, **kwargs)

    def inject_fault(self, service_id: str, fault_class: str, message: str = "injected") -> dict[str, Any]:
        svc = self.services[service_id]
        fault = svc.inject_fault(fault_class, message)
        self.events.append({"event": "fault", "service_id": service_id, "fault": fault.to_dict()})
        if svc.config.restart_on_fault and svc.restart_count < svc.config.max_restarts:
            svc.restart_count += 1
            # Clear to running after digital restart simulation
            if svc.state in (ServiceState.DEGRADED, ServiceState.FAULTED):
                svc.state = ServiceState.RUNNING
            self.events.append(
                {
                    "event": "fault_restart",
                    "service_id": service_id,
                    "restart_count": svc.restart_count,
                }
            )
        return svc.status().to_dict()

    def write_matrix_report(self, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        report = {
            **self.status_all(),
            "schema": "gunnchos.runtime.supervisor_report.v1",
        }
        out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        return out
