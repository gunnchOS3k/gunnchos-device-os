#!/bin/bash
set -e
echo "GunnchOS Phase 0 — Linux desktop prototype starting..."
echo "  Shell: apps/launcher_mock/dist"
echo "  Policy: gunnchos_device_os/"
nginx -g 'daemon off;'
