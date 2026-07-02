# Anime Aggressors — Web Vertical Slice Prototype

**Status:** Vertical slice prototype — **not** the full game.

Original characters **Rook** and **Sage** in a single arena with movement, jump, basic attack, and ring-out placeholder.

## Not included

- Third-party IP, characters, or assets
- Full roster, online multiplayer, save sync, tournaments

## Run locally

```bash
# From repo root
python3 -m http.server 8765 --directory games/anime-aggressors-web

# Or after build copy:
open http://localhost:5173/games/anime-aggressors-web/index.html
```

## Build for launcher

```bash
bash scripts/build_anime_aggressors_web.sh
```

Copies static files to `apps/launcher_mock/public/games/anime-aggressors-web/` for Vite dev/build serving.

## Controls

| Player | Move | Jump | Attack |
|--------|------|------|--------|
| Rook (P1) | A / D | W | J |
| Sage (P2) | ← / → | ↑ | K |
