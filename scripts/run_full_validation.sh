#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== GunnchOS full validation =="

echo "-- Export launcher contract"
python3 scripts/export_launcher_contract.py

echo "-- Check contract freshness"
python3 scripts/check_launcher_contract_fresh.py

echo "-- Python tests (pytest.ini sets pythonpath=src .)"
pytest -q

echo "-- Frontend build + tests"
cd apps/launcher_mock
npm ci 2>/dev/null || npm install
npm run build
npm test

echo "== All validation passed =="
