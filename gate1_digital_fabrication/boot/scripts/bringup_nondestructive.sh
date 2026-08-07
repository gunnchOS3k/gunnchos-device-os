#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
echo "NONDESTRUCTIVE bring-up — no flash"
python3.11 gate1_digital_fabrication/boot/collectors/boot_evidence_collector.py \
  --manifest config/boot/sample_manifest.json || true
PYTHONPATH=.:src python3.11 -m pytest -q tests/test_gate1_boot_probe.py || true
echo "physical_boot_claimed=false"
