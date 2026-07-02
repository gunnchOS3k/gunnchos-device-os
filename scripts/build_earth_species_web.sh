#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/games/earth-species-web"
DEST="$ROOT/apps/launcher_mock/public/games/earth-species-web"

mkdir -p "$DEST"
cp "$SRC/index.html" "$SRC/game.js" "$SRC/style.css" "$DEST/"
echo "Built earth-species-web -> $DEST"
