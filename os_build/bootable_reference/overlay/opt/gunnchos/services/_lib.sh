#!/bin/sh
# Shared helpers for reference service stubs.
svc_start() {
  name="$1"
  pidfile="/run/gunnchos-${name}.pid"
  echo "$$" > "$pidfile"
  echo "started ${name} pid=$$ realm=DEV"
  return 0
}
