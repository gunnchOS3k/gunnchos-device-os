#!/bin/sh
# gunnchOS reference service: dock (supervised real DEV/VM service)
set -eu
. /opt/gunnchos/services/_lib.sh
svc_dispatch "dock" "$@"
