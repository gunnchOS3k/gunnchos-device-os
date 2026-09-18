#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../../../.." && pwd)"
cd "$ROOT"
OUT="artifacts/complete_experience/cx5_0/release_regression/eco010/ECO010_SOAK.json"
exec .venv/bin/python scripts/run_eco010_full_soak.py --duration-sec 1800 --out "$OUT"
