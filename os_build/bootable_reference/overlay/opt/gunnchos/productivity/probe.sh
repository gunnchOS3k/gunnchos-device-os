#!/bin/sh
set -eu
echo GUNNCHOS_PRODUCTIVITY_PROBE=start
test -f /opt/gunnchos/productivity/INSTALL_LEDGER.json
echo GUNNCHOS_PRODUCTIVITY_LEDGER=ok
echo GUNNCHOS_PRODUCTIVITY_PROBE=ok
