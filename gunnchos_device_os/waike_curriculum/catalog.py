"""Accepted WAIKE course IDs — owner truth, not invented aliases.

Source of truth for the 18 IDs:
- ``waike-research-ops/programs/00_program_index.md`` (12 flagship programs)
- additional ``programs/*.md`` files that complete the charter 18
- field-kit charter register ``WAIKE_COURSE_*`` children

Owner markdown is mostly templated or stub; this catalog still uses those IDs so
product depth can be tracked per course instead of one pack-ID browser.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CourseSpec:
    course_id: str
    title: str
    owner_program_file: str
    owner_content_class: str  # TEMPLATED_8WEEK_SHELL | STUB_POINTER | NEAR_TEMPLATE
    level_band: str
    kinesthetic_hook: str


COURSES: tuple[CourseSpec, ...] = (
    CourseSpec(
        "DIGITAL_CONFIDENCE",
        "Digital Confidence to Computer Operator",
        "programs/digital_confidence_to_operator.md",
        "TEMPLATED_8WEEK_SHELL",
        "L0-L2",
        "Hands on a real keyboard: create, copy, and recover a folder tree without a mouse.",
    ),
    CourseSpec(
        "IT_SUPPORT_HARDWARE",
        "IT Support and Hardware Foundations",
        "programs/it_support_hardware.md",
        "TEMPLATED_8WEEK_SHELL",
        "L1-L3",
        "Open a (virtual) ticket, name the failing subsystem, and pick the swap part.",
    ),
    CourseSpec(
        "SOFTWARE_BUILDER",
        "Software Builder Zero-to-Hero",
        "programs/software_builder.md",
        "NEAR_TEMPLATE",
        "L1-L4",
        "Write a tiny function, run its checks, and ship a README that a stranger can run.",
    ),
    CourseSpec(
        "NETWORKING_INFRA",
        "Networking and Internet Infrastructure",
        "programs/networking_infrastructure.md",
        "TEMPLATED_8WEEK_SHELL",
        "L2-L4",
        "Compute a subnet's network address and usable hosts from a CIDR on paper then in code.",
    ),
    CourseSpec(
        "CYBER_SOC",
        "Cybersecurity Foundations and SOC Readiness",
        "programs/cybersecurity_soc.md",
        "TEMPLATED_8WEEK_SHELL",
        "L2-L5",
        "Triage a fake auth log: count bursts, never paste secrets, write a one-line incident note.",
    ),
    CourseSpec(
        "DATA_DASHBOARDS",
        "Data, Databases, and Dashboards",
        "programs/data_databases_dashboards.md",
        "TEMPLATED_8WEEK_SHELL",
        "L2-L4",
        "Fold a CSV into a top-N table you could pin on a Gary lab wall.",
    ),
    CourseSpec(
        "AI_ML_EDGE",
        "AI/ML and Edge AI Foundations",
        "programs/ai_ml_edge.md",
        "TEMPLATED_8WEEK_SHELL",
        "L3-L5",
        "Classify 2-D samples with 1-NN on-device — no cloud round trip.",
    ),
    CourseSpec(
        "EMBEDDED_PROTOTYPING",
        "Embedded Systems and Device Prototyping",
        "programs/embedded_prototyping.md",
        "TEMPLATED_8WEEK_SHELL",
        "L3-L5",
        "Turn a pin list into a GPIO bitmask and explain why pin 0 is special.",
    ),
    CourseSpec(
        "WIRELESS_6G",
        "Wireless, DSP, and 6G Foundations",
        "programs/wireless_6g_foundations.md",
        "TEMPLATED_8WEEK_SHELL",
        "L3-L6",
        "Count OFDM overhead: cyclic prefix vs occupied subcarriers, then say it in one sentence.",
    ),
    CourseSpec(
        "PM_AGILE_LSS",
        "Project Management, Agile, and Lean Six Sigma",
        "programs/pm_agile_lss.md",
        "TEMPLATED_8WEEK_SHELL",
        "L2-L4",
        "Walk a sticky-note critical path; the lab computes the same length.",
    ),
    CourseSpec(
        "GAME_DEV_INTERACTIVE",
        "Game Development and Interactive Media",
        "programs/game_dev_interactive.md",
        "TEMPLATED_8WEEK_SHELL",
        "L2-L4",
        "Move two AABBs until they overlap, then resolve the minimum translation vector.",
    ),
    CourseSpec(
        "SEVEN_GC_APPRENTICESHIP",
        "7GC AI-RAN Research Apprenticeship",
        "programs/seven_gc_apprenticeship.md",
        "TEMPLATED_8WEEK_SHELL",
        "L4-L7",
        "Compute Shannon capacity for a toy RAN slice and write the assumption list.",
    ),
    CourseSpec(
        "CLOUD_DEVOPS",
        "Cloud and DevOps",
        "programs/cloud_and_devops.md",
        "STUB_POINTER",
        "L3-L5",
        "Reject a broken service manifest before it reaches a cluster.",
    ),
    CourseSpec(
        "COMM_PD_ETHICS",
        "Communication, Professional Development, and Ethics",
        "programs/communication_professional_development_and_ethics.md",
        "STUB_POINTER",
        "L1-L3",
        "Redact emails and phones from a peer draft without changing the meaning.",
    ),
    CourseSpec(
        "ROBOTICS_CONTROL",
        "Robotics and Control",
        "programs/robotics_and_control.md",
        "STUB_POINTER",
        "L3-L5",
        "Take one P-controller step toward a heading; feel overshoot vs gain.",
    ),
    CourseSpec(
        "GUNNCHOS_PRODUCT_LAB",
        "gunnchOS Device OS and Product Lab",
        "programs/gunnchos_device_os_and_product_lab.md",
        "STUB_POINTER",
        "L3-L6",
        "Parse a device session JSON and report honest uptime — no fake 100% claims.",
    ),
    CourseSpec(
        "HARDWARE_ENGINEERING",
        "Hardware Engineering",
        "programs/hardware_engineering.md",
        "STUB_POINTER",
        "L3-L5",
        "Build a voltage divider on paper, then let the lab check Vout.",
    ),
    CourseSpec(
        "DATA_VIZ_BI",
        "Data Visualization and Business Intelligence",
        "programs/data_visualization_and_business_intelligence.md",
        "STUB_POINTER",
        "L2-L4",
        "Bin a series into a histogram you could explain to a non-engineer sponsor.",
    ),
)

COURSE_IDS: tuple[str, ...] = tuple(c.course_id for c in COURSES)

LEGACY_PACK_TO_COURSE = {
    "wireless_basics_101": "WIRELESS_6G",
    "waike_gary_upnow_intro": "DIGITAL_CONFIDENCE",
    "python_starter_pack": "SOFTWARE_BUILDER",
}

FACETS = (
    "lessons",
    "assignments",
    "labs",
    "live_repo_linked_labs",
    "group_projects",
    "student_packets",
    "instructor_packets",
    "slide_instruction_media",
    "assessment_mastery",
    "portfolio_outputs",
    "live_gunnchai_tutoring",
    "offline_use",
)

OWNER_REPO = "waike-research-ops"
CONTENT_ROOT_REL = "content/waike/courses"


def course_by_id(course_id: str) -> CourseSpec:
    for spec in COURSES:
        if spec.course_id == course_id:
            return spec
    raise KeyError(course_id)


def resolve_course_id(token: str) -> str:
    """Map a UI/SDK token (course id or legacy pack id) to a catalog course id."""
    if token in COURSE_IDS:
        return token
    if token in LEGACY_PACK_TO_COURSE:
        return LEGACY_PACK_TO_COURSE[token]
    raise KeyError(token)


def catalog_public() -> list[dict[str, Any]]:
    return [
        {
            "course_id": c.course_id,
            "title": c.title,
            "owner_program_file": c.owner_program_file,
            "owner_content_class": c.owner_content_class,
            "level_band": c.level_band,
            "kinesthetic_hook": c.kinesthetic_hook,
        }
        for c in COURSES
    ]
