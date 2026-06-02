#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gunnchos_launcher.campus_modes import load_mode
p = argparse.ArgumentParser()
p.add_argument("--site", required=True)
print(json.dumps(load_mode(p.parse_args().site), indent=2))
