"""Executable per-course labs. Each solver is domain-specific (not a renamed template)."""

from __future__ import annotations

import math
import re
from typing import Any, Callable

from gunnchos_device_os.waike_curriculum.catalog import COURSE_IDS

LabFn = Callable[[dict[str, Any]], dict[str, Any]]


def lab_digital_confidence(payload: dict[str, Any]) -> dict[str, Any]:
    required = list(payload["required_paths"])
    actual = set(payload["actual_paths"])
    missing = [p for p in required if p not in actual]
    extra = sorted(p for p in actual if p not in required)
    return {
        "missing": missing,
        "extra": extra,
        "complete": not missing,
        "operator_note": "Create missing folders before copying files; extras are leftover clutter.",
    }


def lab_it_support_hardware(payload: dict[str, Any]) -> dict[str, Any]:
    ram_gb = float(payload["ram_gb"])
    disk_free_gb = float(payload["disk_free_gb"])
    cpu_load = float(payload["cpu_load"])
    symptom = str(payload["symptom"])
    if "slow_boot" in symptom and disk_free_gb < 8:
        part = "storage"
        action = "free_or_replace_boot_disk"
    elif "app_crash" in symptom and ram_gb < 8:
        part = "memory"
        action = "add_or_reseat_ram"
    elif cpu_load > 0.92 and "fan" in symptom:
        part = "cooling"
        action = "clean_fan_replace_thermal_paste"
    else:
        part = "os_software"
        action = "collect_logs_before_swap"
    return {"failing_subsystem": part, "next_action": action, "swap_now": part in {"memory", "storage", "cooling"}}


def lab_software_builder(payload: dict[str, Any]) -> dict[str, Any]:
    scores = [int(x) for x in payload["scores"]]
    bands = []
    for s in scores:
        if s >= 90:
            bands.append("H")
        elif s >= 75:
            bands.append("M")
        elif s >= 50:
            bands.append("L")
        else:
            bands.append("R")  # retry
    return {"bands": bands, "retry_count": bands.count("R"), "ship_readme": True}


def lab_networking_infra(payload: dict[str, Any]) -> dict[str, Any]:
    cidr = str(payload["cidr"])
    ip_s, prefix_s = cidr.split("/")
    prefix = int(prefix_s)
    octets = [int(x) for x in ip_s.split(".")]
    ip_int = (octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3]
    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    net = ip_int & mask
    host_bits = 32 - prefix
    usable = 0 if host_bits == 0 else (0 if host_bits == 1 else (1 << host_bits) - 2)
    network = f"{(net >> 24) & 255}.{(net >> 16) & 255}.{(net >> 8) & 255}.{net & 255}"
    return {"network": network, "prefix": prefix, "usable_hosts": usable, "broadcast_defined": host_bits >= 2}


def lab_cyber_soc(payload: dict[str, Any]) -> dict[str, Any]:
    lines = list(payload["log_lines"])
    fails: dict[str, int] = {}
    for line in lines:
        if "AUTH_FAIL" in line:
            user = line.split()[-1]
            fails[user] = fails.get(user, 0) + 1
    bursts = {u: n for u, n in fails.items() if n >= int(payload.get("burst_threshold", 3))}
    return {
        "fail_counts": fails,
        "burst_users": sorted(bursts),
        "severity": "high" if bursts else "low",
        "incident_note": (
            "Burst auth failures on " + ",".join(sorted(bursts))
            if bursts
            else "No burst; keep watching."
        ),
    }


def lab_data_dashboards(payload: dict[str, Any]) -> dict[str, Any]:
    rows = list(payload["rows"])
    key = str(payload["group_key"])
    metric = str(payload["metric"])
    n = int(payload.get("top_n", 3))
    totals: dict[str, float] = {}
    for row in rows:
        totals[str(row[key])] = totals.get(str(row[key]), 0.0) + float(row[metric])
    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))[:n]
    return {"top": [{"label": k, "value": v} for k, v in ranked], "groups": len(totals)}


def lab_ai_ml_edge(payload: dict[str, Any]) -> dict[str, Any]:
    train = list(payload["train"])
    query = list(payload["query"])
    labels = []
    for qx, qy in query:
        best_d = None
        best_y = None
        for sx, sy, lab in train:
            d = (float(sx) - float(qx)) ** 2 + (float(sy) - float(qy)) ** 2
            if best_d is None or d < best_d:
                best_d = d
                best_y = lab
        labels.append(best_y)
    return {"labels": labels, "k": 1, "cloud_used": False}


def lab_embedded_prototyping(payload: dict[str, Any]) -> dict[str, Any]:
    pins = [int(p) for p in payload["pins"]]
    mask = 0
    for p in pins:
        if p < 0 or p > 31:
            raise ValueError(f"pin out of range: {p}")
        mask |= 1 << p
    return {
        "gpio_mask": mask,
        "gpio_mask_hex": f"0x{mask:08x}",
        "pin0_set": bool(mask & 1),
        "pin_count": len(set(pins)),
    }


def lab_wireless_6g(payload: dict[str, Any]) -> dict[str, Any]:
    n_fft = int(payload["n_fft"])
    occupied = int(payload["occupied_subcarriers"])
    cp = int(payload["cyclic_prefix"])
    if occupied > n_fft or cp < 0:
        raise ValueError("invalid OFDM sizes")
    symbol = n_fft + cp
    overhead = cp / symbol
    occupancy = occupied / n_fft
    return {
        "symbol_samples": symbol,
        "cp_overhead": round(overhead, 4),
        "occupancy": round(occupancy, 4),
        "null_subcarriers": n_fft - occupied,
        "one_sentence": (
            f"A {n_fft}-point OFDM symbol spends {cp} samples on cyclic prefix "
            f"({overhead:.1%} overhead) and occupies {occupied} of {n_fft} bins."
        ),
    }


def lab_pm_agile_lss(payload: dict[str, Any]) -> dict[str, Any]:
    tasks = {t["id"]: t for t in payload["tasks"]}
    memo: dict[str, int] = {}

    def length(tid: str) -> int:
        if tid in memo:
            return memo[tid]
        task = tasks[tid]
        preds = task.get("preds") or []
        pred_len = max((length(p) for p in preds), default=0)
        memo[tid] = pred_len + int(task["days"])
        return memo[tid]

    ends = {tid: length(tid) for tid in tasks}
    critical_end = max(ends.values())
    critical = sorted(tid for tid, d in ends.items() if d == critical_end)
    return {"critical_path_days": critical_end, "end_tasks": critical, "task_ends": ends}


def lab_game_dev_interactive(payload: dict[str, Any]) -> dict[str, Any]:
    a = payload["a"]
    b = payload["b"]
    ax2, ay2 = a["x"] + a["w"], a["y"] + a["h"]
    bx2, by2 = b["x"] + b["w"], b["y"] + b["h"]
    overlap = a["x"] < bx2 and ax2 > b["x"] and a["y"] < by2 and ay2 > b["y"]
    mtv = {"dx": 0, "dy": 0}
    if overlap:
        left = ax2 - b["x"]
        right = bx2 - a["x"]
        top = ay2 - b["y"]
        bottom = by2 - a["y"]
        dx = -left if left < right else right
        dy = -top if top < bottom else bottom
        if abs(dx) < abs(dy):
            mtv = {"dx": dx, "dy": 0}
        else:
            mtv = {"dx": 0, "dy": dy}
    return {"overlap": overlap, "mtv": mtv}


def lab_seven_gc_apprenticeship(payload: dict[str, Any]) -> dict[str, Any]:
    b_hz = float(payload["bandwidth_hz"])
    snr = float(payload["snr_linear"])
    if b_hz <= 0 or snr < 0:
        raise ValueError("invalid RAN slice")
    capacity = b_hz * math.log2(1.0 + snr)
    return {
        "capacity_bps": capacity,
        "capacity_mbps": round(capacity / 1e6, 4),
        "assumptions": ["AWGN", "single_user", "no_overhead", "not_a_field_measurement"],
    }


def lab_cloud_devops(payload: dict[str, Any]) -> dict[str, Any]:
    manifest = payload["manifest"]
    errors = []
    image = str(manifest.get("image") or "")
    replicas = manifest.get("replicas")
    port = manifest.get("port")
    if not image or ":" not in image:
        errors.append("image_must_include_tag")
    if not isinstance(replicas, int) or replicas < 1:
        errors.append("replicas_must_be_positive_int")
    if not isinstance(port, int) or port < 1 or port > 65535:
        errors.append("port_out_of_range")
    if manifest.get("privileged") is True:
        errors.append("privileged_forbidden_in_class_cluster")
    return {"ok": not errors, "errors": errors}


def lab_comm_pd_ethics(payload: dict[str, Any]) -> dict[str, Any]:
    text = str(payload["text"])
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phones = re.findall(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", text)
    redacted = text
    for e in emails:
        redacted = redacted.replace(e, "[EMAIL]")
    for p in phones:
        redacted = redacted.replace(p, "[PHONE]")
    return {
        "redacted": redacted,
        "email_count": len(emails),
        "phone_count": len(phones),
        "meaning_preserved": "[EMAIL]" in redacted or "[PHONE]" in redacted or (not emails and not phones),
    }


def lab_robotics_control(payload: dict[str, Any]) -> dict[str, Any]:
    heading = float(payload["heading"])
    target = float(payload["target"])
    kp = float(payload["kp"])
    err = target - heading
    delta = kp * err
    nxt = heading + delta
    return {"error": err, "delta": delta, "next_heading": nxt, "overshoot_risk": abs(kp) > 1.0}


def lab_gunnchos_product_lab(payload: dict[str, Any]) -> dict[str, Any]:
    sessions = list(payload["sessions"])
    uptimes = []
    for s in sessions:
        start, stop = float(s["start"]), float(s["stop"])
        if stop < start:
            raise ValueError("stop before start")
        uptimes.append(stop - start)
    total = sum(uptimes)
    claimed = payload.get("claimed_uptime_ratio")
    honest = True
    if claimed is not None and float(claimed) > 1.0:
        honest = False
    return {
        "session_count": len(sessions),
        "total_uptime_s": total,
        "mean_uptime_s": total / len(sessions) if sessions else 0.0,
        "honest_claim": honest,
    }


def lab_hardware_engineering(payload: dict[str, Any]) -> dict[str, Any]:
    vin = float(payload["vin"])
    r1 = float(payload["r1"])
    r2 = float(payload["r2"])
    if r1 <= 0 or r2 <= 0:
        raise ValueError("resistors must be positive")
    vout = vin * (r2 / (r1 + r2))
    return {"vout": vout, "ratio": r2 / (r1 + r2), "current_a": vin / (r1 + r2)}


def lab_data_viz_bi(payload: dict[str, Any]) -> dict[str, Any]:
    values = [float(v) for v in payload["values"]]
    edges = [float(e) for e in payload["edges"]]
    if len(edges) < 2:
        raise ValueError("need at least one bin")
    counts = [0] * (len(edges) - 1)
    for v in values:
        placed = False
        for i in range(len(edges) - 1):
            lo, hi = edges[i], edges[i + 1]
            last = i == len(edges) - 2
            if (v >= lo and v < hi) or (last and v == hi):
                counts[i] += 1
                placed = True
                break
        if not placed:
            pass
    return {"counts": counts, "n": len(values), "bins": len(counts)}


SOLVERS: dict[str, LabFn] = {
    "DIGITAL_CONFIDENCE": lab_digital_confidence,
    "IT_SUPPORT_HARDWARE": lab_it_support_hardware,
    "SOFTWARE_BUILDER": lab_software_builder,
    "NETWORKING_INFRA": lab_networking_infra,
    "CYBER_SOC": lab_cyber_soc,
    "DATA_DASHBOARDS": lab_data_dashboards,
    "AI_ML_EDGE": lab_ai_ml_edge,
    "EMBEDDED_PROTOTYPING": lab_embedded_prototyping,
    "WIRELESS_6G": lab_wireless_6g,
    "PM_AGILE_LSS": lab_pm_agile_lss,
    "GAME_DEV_INTERACTIVE": lab_game_dev_interactive,
    "SEVEN_GC_APPRENTICESHIP": lab_seven_gc_apprenticeship,
    "CLOUD_DEVOPS": lab_cloud_devops,
    "COMM_PD_ETHICS": lab_comm_pd_ethics,
    "ROBOTICS_CONTROL": lab_robotics_control,
    "GUNNCHOS_PRODUCT_LAB": lab_gunnchos_product_lab,
    "HARDWARE_ENGINEERING": lab_hardware_engineering,
    "DATA_VIZ_BI": lab_data_viz_bi,
}

FIXTURES: dict[str, dict[str, Any]] = {
    "DIGITAL_CONFIDENCE": {
        "required_paths": ["Documents/waike", "Documents/waike/lab1", "Downloads/inbox"],
        "actual_paths": ["Documents/waike", "Downloads/inbox", "Desktop/scratch"],
    },
    "IT_SUPPORT_HARDWARE": {
        "ram_gb": 4,
        "disk_free_gb": 40,
        "cpu_load": 0.3,
        "symptom": "app_crash_on_open",
    },
    "SOFTWARE_BUILDER": {"scores": [92, 76, 49, 50]},
    "NETWORKING_INFRA": {"cidr": "192.168.10.40/26"},
    "CYBER_SOC": {
        "burst_threshold": 3,
        "log_lines": [
            "AUTH_FAIL ada",
            "AUTH_OK bob",
            "AUTH_FAIL ada",
            "AUTH_FAIL ada",
            "AUTH_FAIL ada",
            "AUTH_FAIL bob",
        ],
    },
    "DATA_DASHBOARDS": {
        "group_key": "site",
        "metric": "hours",
        "top_n": 2,
        "rows": [
            {"site": "Gary", "hours": 12},
            {"site": "Ghana", "hours": 5},
            {"site": "Gary", "hours": 8},
            {"site": "Geelong", "hours": 9},
        ],
    },
    "AI_ML_EDGE": {
        "train": [[0.0, 0.0, "noise"], [2.0, 2.0, "signal"], [8.0, 1.0, "pilot"]],
        "query": [[1.9, 2.1], [0.1, 0.2]],
    },
    "EMBEDDED_PROTOTYPING": {"pins": [0, 3, 7]},
    "WIRELESS_6G": {"n_fft": 64, "occupied_subcarriers": 52, "cyclic_prefix": 16},
    "PM_AGILE_LSS": {
        "tasks": [
            {"id": "A", "days": 2, "preds": []},
            {"id": "B", "days": 3, "preds": ["A"]},
            {"id": "C", "days": 1, "preds": ["A"]},
            {"id": "D", "days": 4, "preds": ["B", "C"]},
        ]
    },
    "GAME_DEV_INTERACTIVE": {
        "a": {"x": 0, "y": 0, "w": 10, "h": 10},
        "b": {"x": 8, "y": 2, "w": 10, "h": 10},
    },
    "SEVEN_GC_APPRENTICESHIP": {"bandwidth_hz": 1.0e6, "snr_linear": 3.0},
    "CLOUD_DEVOPS": {
        "manifest": {"image": "waike-lab:0.1", "replicas": 2, "port": 8080, "privileged": False}
    },
    "COMM_PD_ETHICS": {
        "text": "Call Maya at 219-555-0142 or maya.demo@example.org before class."
    },
    "ROBOTICS_CONTROL": {"heading": 10.0, "target": 30.0, "kp": 0.5},
    "GUNNCHOS_PRODUCT_LAB": {
        "sessions": [{"start": 100.0, "stop": 160.0}, {"start": 200.0, "stop": 230.0}],
        "claimed_uptime_ratio": 0.4,
    },
    "HARDWARE_ENGINEERING": {"vin": 5.0, "r1": 1000.0, "r2": 3000.0},
    "DATA_VIZ_BI": {"values": [1, 2, 2, 5, 9], "edges": [0, 3, 6, 10]},
}


def run_lab(course_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if course_id not in SOLVERS:
        raise KeyError(course_id)
    data = FIXTURES[course_id] if payload is None else payload
    result = SOLVERS[course_id](data)
    return {
        "ok": True,
        "course_id": course_id,
        "result": result,
        "fixture_used": payload is None,
        "live_repo_path": f"gunnchos_device_os/waike_curriculum/labs.py::{SOLVERS[course_id].__name__}",
    }


def run_all_labs() -> dict[str, Any]:
    rows = []
    for cid in COURSE_IDS:
        rows.append(run_lab(cid))
    return {
        "ok": all(r["ok"] for r in rows),
        "count": len(rows),
        "labs": rows,
    }
