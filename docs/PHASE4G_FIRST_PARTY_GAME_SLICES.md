# GunnchOS Phase 4G — Foot Racing & Earth Species Playable Web Prototypes

**Branch:** `phase4g-foot-racing-earth-species-prototypes`  
**Depends on:** Phase 2D/2E game launch adapter + Anime Aggressors web path  
**Issues:** OS-006 (game vertical slices)

## Real after this PR

- `games/foot-racing-web/` — original-character sprint prototype (Bolt, lanes, boost, obstacles, finish)
- `games/earth-species-web/` — original species exploration prototype (Nora, artifacts, fact cards)
- Build scripts copy both to launcher `public/games/`
- Game Mode marks Foot Racing and Earth Species as `playable_web_build`
- Launch opens `/games/foot-racing-web/index.html` and `/games/earth-species-web/index.html`

## Still prototype

- Not the full games — single track / small map, keyboard only
- No save sync, online multiplayer, or native builds
- Earth Species citations are placeholders pending verified sources

## Original IP only

All characters and species are first-party fictional IP. No third-party franchises (Mario, Kirby, Sonic, Pokemon, Nintendo, etc.).

## Validation

```bash
bash scripts/build_foot_racing_web.sh
bash scripts/build_earth_species_web.sh
make validate-full
```
