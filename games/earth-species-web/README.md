# Earth Species — Web Vertical Slice Prototype

**Status:** Vertical slice prototype — **not** the full game.

Original explorer **Nora** roams a small map, collects species artifacts, and reads educational fact cards with citation placeholders.

## Species in this slice

| Species | Habitat |
|---------|---------|
| Coral Finch | Sunlit meadow edges |
| Moss Turtle | Shaded pond banks |
| Star Orchid | Forest understory |
| Ridge Fox | Rocky highland trail |

All species are **original fictional IP** — not based on real trademarked characters or franchises.

## Not included

- Third-party IP or real-world licensed content
- Full RPG progression, quests, cloud saves, native build

## Run locally

```bash
# From repo root
python3 -m http.server 8765 --directory games/earth-species-web

# Or after build copy:
open http://localhost:5173/games/earth-species-web/index.html
```

## Build for launcher

```bash
bash scripts/build_earth_species_web.sh
```

Copies static files to `apps/launcher_mock/public/games/earth-species-web/` for Vite dev/build serving.

## Controls

| Action | Key |
|--------|-----|
| Move | WASD or arrow keys |
| Collection log | I |
| Close card / log | Close button |
