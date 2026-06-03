FORBIDDEN = {'user_id', 'email'}

def filter_packet(p: dict) -> dict:
    return {k:v for k,v in p.items() if k not in FORBIDDEN}
