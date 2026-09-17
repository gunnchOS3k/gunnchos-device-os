"""Consent / privacy helpers. Minors mode disabled by default."""

from __future__ import annotations

from typing import Any, Dict

from gunnchos_device_os.cx4_validation_center.contracts import ConsentState, _now

MINORS_MODE_DISABLED_BY_DEFAULT = True

CONSENT_PLAIN_LANGUAGE = """
This Validation Center session collects task ratings, comments, and optional evidence
to improve gunnchOS. You may stop at any time. We use a participant alias, not your
legal name, by default. Data is stored locally on this device unless a moderator
explicitly configures otherwise. Photo, audio, and video are optional and require
separate consent. Do not share passwords or personal portfolio content.
""".strip()


def normalize_consent(raw: Dict[str, Any]) -> Dict[str, Any]:
    declined = bool(raw.get("declined"))
    accepted = bool(raw.get("accepted")) and not declined
    minors = bool(raw.get("minors_mode", False))
    if MINORS_MODE_DISABLED_BY_DEFAULT and minors and not raw.get("approved_minors_workflow"):
        # Explicit approved workflow required; otherwise force disabled
        minors = False
    state = ConsentState(
        accepted=accepted,
        declined=declined,
        purpose_acknowledged=bool(raw.get("purpose_acknowledged", accepted)),
        media_photo=bool(raw.get("media_photo")) if accepted else False,
        media_audio=bool(raw.get("media_audio")) if accepted else False,
        media_video=bool(raw.get("media_video")) if accepted else False,
        recorded_at=_now() if (accepted or declined) else None,
        minors_mode=minors,
        plain_language_shown=bool(raw.get("plain_language_shown", True)),
    )
    return state.to_dict()
