"""Base types for gunnchOS digital runtime services."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable
import json
import time
from pathlib import Path


CLAIM_BOUNDARY = (
    "In-process digital runtime service architecture only. Not systemd, "
    "not a kernel init, not a shipping OS process supervisor, and not a "
    "FULL_OPERATIONAL_PRODUCT claim."
)


class ServiceState(str, Enum):
    UNINITIALIZED = "uninitialized"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    FAULTED = "faulted"
    STOPPED = "stopped"


@dataclass
class ServiceConfig:
    """Per-service configuration blob (JSON-serializable)."""

    service_id: str
    enabled: bool = True
    options: dict[str, Any] = field(default_factory=dict)
    persistence_path: str | None = None
    restart_on_fault: bool = True
    max_restarts: int = 3

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServiceConfig":
        return cls(
            service_id=str(data["service_id"]),
            enabled=bool(data.get("enabled", True)),
            options=dict(data.get("options") or {}),
            persistence_path=data.get("persistence_path"),
            restart_on_fault=bool(data.get("restart_on_fault", True)),
            max_restarts=int(data.get("max_restarts", 3)),
        )


@dataclass
class FaultRecord:
    service_id: str
    fault_class: str
    message: str
    timestamp: float = field(default_factory=time.time)
    recoverable: bool = True
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ServiceStatus:
    service_id: str
    state: ServiceState
    deps: list[str] = field(default_factory=list)
    api_surface: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    persistence: dict[str, Any] = field(default_factory=dict)
    faults: list[dict[str, Any]] = field(default_factory=list)
    restart_count: int = 0
    started_at: float | None = None
    health: str = "unknown"
    claim_boundary: str = CLAIM_BOUNDARY

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value
        return d


class RuntimeService:
    """Minimal lifecycle contract for digital services."""

    service_id: str = "base"
    dependencies: list[str] = []
    api_surface: list[str] = []

    def __init__(self, config: ServiceConfig | None = None) -> None:
        self.config = config or ServiceConfig(service_id=self.service_id)
        self.state = ServiceState.UNINITIALIZED
        self.faults: list[FaultRecord] = []
        self.restart_count = 0
        self.started_at: float | None = None
        self._store: dict[str, Any] = {}

    def configure(self, options: dict[str, Any] | None = None) -> dict[str, Any]:
        if options:
            self.config.options.update(options)
        return dict(self.config.options)

    def persist(self) -> dict[str, Any]:
        path = self.config.persistence_path
        payload = {
            "service_id": self.service_id,
            "state": self.state.value,
            "store": dict(self._store),
            "options": dict(self.config.options),
            "faults": [f.to_dict() for f in self.faults[-20:]],
        }
        if path:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return {"persisted": bool(path), "path": path, "keys": sorted(self._store.keys())}

    def restore(self) -> dict[str, Any]:
        path = self.config.persistence_path
        if not path or not Path(path).exists():
            return {"restored": False, "reason": "no_persistence"}
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self._store = dict(data.get("store") or {})
        self.config.options.update(dict(data.get("options") or {}))
        return {"restored": True, "keys": sorted(self._store.keys())}

    def start(self) -> ServiceStatus:
        self.state = ServiceState.STARTING
        try:
            self.restore()
            self.on_start()
            self.state = ServiceState.RUNNING
            self.started_at = time.time()
            self.persist()
        except Exception as exc:  # noqa: BLE001 — fault channel
            self.record_fault("start_failure", str(exc), recoverable=True)
            self.state = ServiceState.FAULTED
        return self.status()

    def stop(self) -> ServiceStatus:
        try:
            self.on_stop()
        except Exception as exc:  # noqa: BLE001
            self.record_fault("stop_failure", str(exc), recoverable=True)
        self.persist()
        self.state = ServiceState.STOPPED
        return self.status()

    def on_start(self) -> None:
        """Subclass hook."""

    def on_stop(self) -> None:
        """Subclass hook."""

    def health_check(self) -> str:
        if self.state == ServiceState.RUNNING:
            return "ok"
        if self.state == ServiceState.DEGRADED:
            return "degraded"
        if self.state == ServiceState.FAULTED:
            return "faulted"
        return "not_running"

    def record_fault(
        self,
        fault_class: str,
        message: str,
        *,
        recoverable: bool = True,
        detail: dict[str, Any] | None = None,
    ) -> FaultRecord:
        fault = FaultRecord(
            service_id=self.service_id,
            fault_class=fault_class,
            message=message,
            recoverable=recoverable,
            detail=detail or {},
        )
        self.faults.append(fault)
        if self.state == ServiceState.RUNNING:
            self.state = ServiceState.DEGRADED if recoverable else ServiceState.FAULTED
        return fault

    def inject_fault(self, fault_class: str, message: str = "injected") -> FaultRecord:
        return self.record_fault(fault_class, message, recoverable=True, detail={"injected": True})

    def api(self, method: str, **kwargs: Any) -> Any:
        handler = getattr(self, f"api_{method}", None)
        if handler is None or not callable(handler):
            raise KeyError(f"unknown API method: {method}")
        return handler(**kwargs)

    def status(self) -> ServiceStatus:
        return ServiceStatus(
            service_id=self.service_id,
            state=self.state,
            deps=list(self.dependencies),
            api_surface=list(self.api_surface),
            config=self.config.to_dict(),
            persistence={
                "path": self.config.persistence_path,
                "keys": sorted(self._store.keys()),
            },
            faults=[f.to_dict() for f in self.faults],
            restart_count=self.restart_count,
            started_at=self.started_at,
            health=self.health_check(),
        )


# Factory type for catalog registration
ServiceFactory = Callable[[ServiceConfig], RuntimeService]
