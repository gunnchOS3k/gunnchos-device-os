#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-artifacts/complete_experience/cx4_0/human_a11y}"
mkdir -p "$OUT"/{screenshots,logs,forms,issues}
echo "Prepared evidence folders under $OUT (no PASS claimed)"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/PREPARED_AT_UTC.txt"
