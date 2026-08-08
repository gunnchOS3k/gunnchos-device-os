#!/bin/sh
# gunnchOS reference service: a11y (supervised real DEV/VM service)
set -eu
. /opt/gunnchos/services/_lib.sh
svc_dispatch "a11y" "$@"
