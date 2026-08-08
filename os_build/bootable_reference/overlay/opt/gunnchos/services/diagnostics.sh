#!/bin/sh
# gunnchOS reference service: diagnostics (supervised real DEV/VM service)
set -eu
. /opt/gunnchos/services/_lib.sh
svc_dispatch "diagnostics" "$@"
