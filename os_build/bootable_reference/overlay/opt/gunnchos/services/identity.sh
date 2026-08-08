#!/bin/sh
# gunnchOS reference service: identity (supervised real DEV/VM service)
set -eu
. /opt/gunnchos/services/_lib.sh
svc_dispatch "identity" "$@"
