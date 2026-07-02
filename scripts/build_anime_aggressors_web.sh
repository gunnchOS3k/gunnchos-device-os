#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/games/anime-aggressors-web"
DEST="$ROOT/apps/launcher_mock/public/games/anime-aggressors-web"

mkdir -p "$DEST"
cp "$SRC/index.html" "$SRC/game.js" "$SRC/style.css" "$DEST/"
echo "Built anime-aggressors-web -> $DEST"
