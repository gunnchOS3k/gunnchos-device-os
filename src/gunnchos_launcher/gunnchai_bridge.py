"""gunnchAI3k tutor action stub."""


def tutor_action(lesson: str = "waike_intro") -> dict:
    return {
        "tutor": "gunnchAI3k",
        "action": "explain",
        "lesson": lesson,
        "offline_capable": True,
        "note": "mock — integrate with gunnchAI3k repo tutor engine",
    }
