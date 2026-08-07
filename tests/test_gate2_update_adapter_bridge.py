from pathlib import Path
import importlib.util
p = Path(__file__).resolve().parents[1] / "gate2_nonphysical" / "update_adapter_bridge.py"
spec = importlib.util.spec_from_file_location("update_adapter_bridge", p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
assert mod.PHYSICAL_STATUS == "PHYSICAL_PENDING"
assert "emulator" in mod.ADAPTERS
