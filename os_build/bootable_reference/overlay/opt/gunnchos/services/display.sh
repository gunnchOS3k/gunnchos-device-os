#!/bin/sh
# gunnchOS reference service: display (supervised real DEV/VM service)
set -eu
. /opt/gunnchos/services/_lib.sh
svc_dispatch "display" "$@"
