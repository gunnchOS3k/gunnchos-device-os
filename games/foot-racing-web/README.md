# Foot Racing — Web Vertical Slice Prototype

**Status:** Vertical slice prototype — **not** the full game.

Original character **Bolt** sprints through a three-lane track with boost meter, obstacles, timer, and finish line.

## Not included

- Third-party IP, characters, or assets
- Multiplayer, leaderboards, track editor, native build

## Run locally

```bash
# From repo root
python3 -m http.server 8765 --directory games/foot-racing-web

# Or after build copy:
open http://localhost:5173/games/foot-racing-web/index.html
```

## Build for launcher

```bash
bash scripts/build_foot_racing_web.sh
```

Copies static files to `apps/launcher_mock/public/games/foot-racing-web/` for Vite dev/build serving.

## Controls

| Action | Key |
|--------|-----|
| Change lane left | ← |
| Change lane right | → |
| Accelerate | ↑ |
| Sprint / boost | Space |
