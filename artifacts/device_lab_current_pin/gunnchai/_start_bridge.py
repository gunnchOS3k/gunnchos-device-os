
import os, sys
from pathlib import Path
sys.path.insert(0, '/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os/.worktrees/device-lab-post-waike-closure')
os.environ['GUNNCHAI_PRODUCT_SERVICE_URL'] = 'http://127.0.0.1:18791'
os.environ['GUNNCHAI_REQUIRE_LIVE_ASSIST'] = '1'
from gunnchos_device_os.first_party_apps.companion_bridge import start_bridge
from gunnchos_device_os.first_party_apps import runtime
repo = Path('/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os/.worktrees/device-lab-post-waike-closure')
data = Path('/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os/.worktrees/device-lab-post-waike-closure/artifacts/device_lab_current_pin/gunnchai/companion_sandbox')
data.mkdir(parents=True, exist_ok=True)
# Align first-party sandbox with bridge data dir
os.environ['GUNNCHOS_SANDBOX_DATA_DIR'] = str(data)
os.environ['GUNNCHOS_APP_PERMISSIONS'] = 'storage_read,storage_write,ai_interface'
server, base = start_bridge(repo, data, host='127.0.0.1', port=18765)
print('bridge_listening', base, flush=True)
import time
while True:
    time.sleep(3600)
