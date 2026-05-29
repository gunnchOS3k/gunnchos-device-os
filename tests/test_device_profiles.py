import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gunnchos_launcher.device_profile import get_profile

def test_student_school():
    p = get_profile("student_14_5", "school")
    assert p["offline_ready"]
