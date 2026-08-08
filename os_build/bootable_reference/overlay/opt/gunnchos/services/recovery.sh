#!/bin/sh
# gunnchOS reference service: recovery (supervised real DEV/VM service)
set -eu
. /opt/gunnchos/services/_lib.sh
svc_dispatch "recovery" "$@"
