#!/bin/sh
set -eu
ACTIVE=$(cat /var/lib/gunnchos/state/active_slot 2>/dev/null || echo a)
A=$(cat /var/lib/gunnchos/slot_a/version 2>/dev/null || echo unknown)
B=$(cat /var/lib/gunnchos/slot_b/version 2>/dev/null || echo unknown)
echo "GUNNCHOS_UPDATER_AB active=${ACTIVE} slot_a=${A} slot_b=${B} signing=DEV_HMAC_STUB_ONLY"
