def research_measurement_guard(profile: dict) -> bool:
    return profile.get('mode') == 'research_measurement'
