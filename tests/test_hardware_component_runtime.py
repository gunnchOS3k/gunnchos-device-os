from pathlib import Path
import subprocess
import sys


def test_component_runtime_simulation():
    root = Path(__file__).resolve().parents[1]
    r = subprocess.run([sys.executable, "hardware_component_runtime/scripts/simulate_os_on_component_stack.py"], cwd=root)
    assert r.returncode == 0


def test_component_stack_sync_fixtures():
    root = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [sys.executable, "hardware_component_runtime/scripts/sync_component_stacks.py", "--use-fixtures"],
        cwd=root,
    )
    assert r.returncode == 0
