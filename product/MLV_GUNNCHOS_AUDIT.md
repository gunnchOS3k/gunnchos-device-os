# gunnchOS audit for 3k MLV integration

**Accepted main SHA:** `2218ead0efa0e4b8a622717a0a9bf623ee95ddb0`  
**Worktree branch:** `integration/3k-mlv-world-workspace-v1`  
**Owner checkout:** left on dirty `vxp/vxp-0-vxp-1-living-workspace` — not modified.

## Before this slice

- Canonical app registry: `gunnchos_device_os/app_registry.py` — no MLV entry
- Display-name registry: `src/gunnchos_launcher/app_registry.py` — no "My Little Vicinity"
- Bridges exist for 7GC, Edge-IO, gunnchAI — no `mlv_bridge.py`
- Deep-link precedent: `gunnchos_device_os/learning_os/deep_link.py` (`waike://`)
- Journey presets: twelve presets, youth/library/guardian rules in place
- Shared contracts exist; no `mlv_artifact_intent.schema.json`
- No `product/MLV_WORLD_WORKSPACE_REQUIREMENTS.md`

## After this slice (uncommitted)

- MLV registered in both registries
- `src/gunnchos_launcher/mlv_bridge.py` + tests
- Artifact intent schema + tests
- Journey preset allowlists updated without enabling Guardian/Classroom/Scooter/Bicycle
- Claim-boundary language added

## Not done

- Live Pixel / browser / PWA smoke
- Draft PR
- Wiring launcher_mock UI chrome beyond registry
- Production identity SSO replacement of GitHub OAuth
