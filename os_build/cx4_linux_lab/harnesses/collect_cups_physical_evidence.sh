#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-artifacts/complete_experience/cx4_0/physical_printer}"
mkdir -p "$OUT"
{
  echo "=== lpstat -t ==="; lpstat -t 2>&1 || true
  echo "=== lpstat -v ==="; lpstat -v 2>&1 || true
  echo "=== cups config ==="; ls /etc/cups 2>&1 || true
  echo "=== job history ==="; lpstat -W completed -o 2>&1 || true
  echo "=== error log tail ==="; tail -n 100 /var/log/cups/error_log 2>&1 || true
} > "$OUT/cups_collector_$(date -u +%Y%m%dT%H%M%SZ).txt"
echo "PHYSICAL_PRINTER_PENDING=true" > "$OUT/STATUS.txt"
echo "Collector ran; physical PASS not claimed"
