def generate_spdx(path):
    import json
    from pathlib import Path
    data = {'spdxVersion': '2.3', 'name': 'gunnchos-device-os'}
    Path(path).write_text(json.dumps(data, indent=2))
