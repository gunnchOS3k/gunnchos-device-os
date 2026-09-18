#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-artifacts/complete_experience/cx4_0/av}"
mkdir -p "$OUT"
{
  echo "=== v4l2 ==="; v4l2-ctl --list-devices 2>&1 || true
  echo "=== pw-cli ==="; pw-cli ls 2>&1 | head -200 || true
  echo "=== wpctl ==="; wpctl status 2>&1 || true
  echo "=== pactl ==="; pactl info 2>&1 || true
} > "$OUT/av_diag_$(date -u +%Y%m%dT%H%M%SZ).txt"
echo "PHYSICAL_CAMERA_MIC_AV_PENDING=true" > "$OUT/STATUS.txt"
