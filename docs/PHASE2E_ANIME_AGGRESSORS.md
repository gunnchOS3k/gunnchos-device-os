# GunnchOS Phase 2E — Anime Aggressors Playable Web Prototype

**Branch:** `phase2e-anime-aggressors-web-build-path`  
**Depends on:** Phase 2D (`phase2d-game-launch-adapter`)  
**Issues:** OS-006

## Real after this PR

- `games/anime-aggressors-web/` — original-character arena vertical slice
- Build script copies to launcher `public/games/`
- Game Mode marks Anime Aggressors as `playable_web_build`
- Launch opens `/games/anime-aggressors-web/index.html`

## Still prototype

- Not the full game — one arena, two placeholders, keyboard only
- No save sync, online, or native build

## Validation

```bash
bash scripts/build_anime_aggressors_web.sh
make validate-full
```
