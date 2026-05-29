def is_allowed(app_id: str, profile: dict) -> bool:
    return profile.get('mode') != 'school' or app_id in ['WAIKE Classroom']
