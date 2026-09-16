
import os, sys
from pathlib import Path
sys.path.insert(0, '/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os/.worktrees/device-lab-current-pin-revalidation/.deps/current-pin-waike-lp/services/hub')
os.environ['WAIKE_ROOT'] = '/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/waike-research-ops'
os.environ['WAIKE_SEED_TEST_FIXTURES'] = '1'
os.environ['WAIKE_ENV'] = 'development'
import uvicorn
from app.main import HubConfig, create_app
app = create_app(
    HubConfig(production_auth_enabled=True, fixture_auth_enabled=False),
    db_path=Path('/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os/.worktrees/device-lab-current-pin-revalidation/artifacts/device_lab_current_pin/waike/gui_journey/hub_sidecar/hub_device_lab.sqlite'),
    seed=True,
)
# Force h11: httptools can stall behind QEMU guestfwd even when TCP accepts.
uvicorn.run(
    app,
    host='127.0.0.1',
    port=8787,
    log_level='info',
    http='h11',
    loop='asyncio',
    timeout_keep_alive=1,
)
