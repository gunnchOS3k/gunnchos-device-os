#!/bin/sh
# gunnchOS reference service: profile_manager (supervised real DEV/VM service)
set -eu
. /opt/gunnchos/services/_lib.sh
svc_dispatch "profile_manager" "$@"
