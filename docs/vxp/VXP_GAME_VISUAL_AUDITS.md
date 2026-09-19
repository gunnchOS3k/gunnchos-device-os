# Game Visual Audits (read-only) — VXP-2..5 planning

Captured LIVE 2026-09-18. Secondary repos were **not** mutated.

## SHA discrepancy vs checkpoint

| Repo | Checkpoint | LIVE |
|---|---|---|
| anime-aggressors | `85418e99…` | `789b229406bef24d0a614309f84ef08e605fec6c` |
| pedestrian-pursuit | `e0c21fcc…` | `599c6b320d7c2d2340ead82f74f085a7b17939fc` |
| archive-of-life-artifact-world | `a2145ca6…` | `89f0bb447c27b250ee67c3c21549c1b4b3278c7d` |
| beatlink-party | `22a21a41…` | `b20a570a817398078430f8fa2761b1d1fe8cf89c` |

## Anime Aggressors (VXP-2 candidate)

- Strong 1024 elemental seal; **wordmark PENDING**
- Menu still engineer grid; leverage navy/gold + elemental accents
- Ban procedural/proxy copy from player-facing chrome

## Pedestrian Pursuit (VXP-3 candidate)

- Strong sneaker launcher; HUD still label-heavy graybox
- Art pack under `assets/art/ui/` unused as brand chrome — wire for VXP-3
- Keep a11y spine; strip engineer subtitle copy

## Archive of Life (VXP-4 candidate)

- Specimen-card mark thin; emoji-dense field HUD is primary failure
- Sage/gold/cream forest language; replace emoji with drawn glyphs
- Keep honesty labels as designed chips

## BeatLink Party (VXP-5 candidate)

- Lo-fi EQ favicon; purple club gradient risks generic AI party look
- Replace emoji hype controls; treat room code as branded ticket
- Vectorize EQ + wordmark; allow pinch zoom

## Shared

All four: `CANONICAL_LOGO_ASSET_PENDING` for full wordmarks. Next single lane after VXP-1: **VXP-2 Anime Aggressors brand system** (do not start in this PR).
