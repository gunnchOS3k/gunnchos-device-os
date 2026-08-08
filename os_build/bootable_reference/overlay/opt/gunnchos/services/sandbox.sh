#!/bin/sh
# gunnchOS reference service: sandbox (supervised real DEV/VM service)
set -eu
. /opt/gunnchos/services/_lib.sh
svc_dispatch "sandbox" "$@"
