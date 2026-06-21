"""User profile schema for the user-focused OS experience layer."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

AgeBand = Literal[
    "pre_k", "elementary", "middle_school", "high_school",
    "undergraduate", "graduate", "postdoc", "adult", "senior",
]
SkillLevel = Literal["first_time_user", "beginner", "intermediate", "advanced", "expert"]
CustomizationDepth = Literal["simple", "guided", "full", "power_user"]


@dataclass
class UserProfile:
    user_id: str
    display_name: str
    age_band: AgeBand
    persona: str
    journey_preset: str
    preferred_language: str = "en"
    reading_level: str = "grade_level"
    accessibility_needs: list[str] = field(default_factory=list)
    input_preferences: list[str] = field(default_factory=lambda: ["touch"])
    creative_interests: list[str] = field(default_factory=list)
    learning_goals: list[str] = field(default_factory=list)
    work_goals: list[str] = field(default_factory=list)
    gaming_preferences: list[str] = field(default_factory=list)
    privacy_level: str = "standard"
    guardian_required: bool = False
    offline_first: bool = False
    skill_level: SkillLevel = "beginner"
    customization_depth: CustomizationDepth = "simple"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserProfile:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.user_id:
            errors.append("user_id is required")
        if not self.display_name:
            errors.append("display_name is required")
        if not self.persona:
            errors.append("persona is required")
        if not self.journey_preset:
            errors.append("journey_preset is required")
        return errors
