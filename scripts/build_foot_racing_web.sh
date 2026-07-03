#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/games/foot-racing-web"
DEST="$ROOT/apps/launcher_mock/public/games/foot-racing-web"

mkdir -p "$DEST"
cp "$SRC/index.html" "$SRC/game.js" "$SRC/style.css" "$DEST/"
echo "Built foot-racing-web -> $DEST"
