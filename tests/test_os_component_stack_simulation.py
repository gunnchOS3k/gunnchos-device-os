from pathlib import Path
import subprocess
import sys


def test_os_component_stack_simulation_output():
    root = Path(__file__).resolve().parents[1]
    out = root / "hardware_component_runtime/results/os_component_runtime_simulation.json"
    subprocess.run([sys.executable, "hardware_component_runtime/scripts/simulate_os_on_component_stack.py"], cwd=root, check=True)
    assert out.exists()
    text = out.read_text()
    assert "student_14_5" in text
    assert "wsl_path" in text
