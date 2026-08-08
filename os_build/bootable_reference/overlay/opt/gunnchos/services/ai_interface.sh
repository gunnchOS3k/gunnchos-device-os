#!/bin/sh
# gunnchOS reference service: ai_interface (supervised real DEV/VM service)
set -eu
. /opt/gunnchos/services/_lib.sh
svc_dispatch "ai_interface" "$@"
