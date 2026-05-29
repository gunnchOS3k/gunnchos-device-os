def deploy(package_id: str, target_device: str) -> dict:
    return {'package_id': package_id, 'target': target_device, 'transport': 'wifi_or_usbc'}
