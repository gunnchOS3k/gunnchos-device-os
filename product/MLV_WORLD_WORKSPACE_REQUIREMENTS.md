# My Little Vicinity — World Workspace requirements

**Status:** device OS alpha · prototype World Workspace integration  
**Paired branch:** `3k-mlv` `revival/gunnchos-world-workspace-v1`  
**Accepted device-os base:** `2218ead0efa0e4b8a622717a0a9bf623ee95ddb0`

## Authority split

gunnchOS remains responsible for identity, launcher, journey presets, privacy/youth/library policy, offline policy, accessibility, and app capability.

3k MLV is the optional spatial presentation layer. The renderer is **not** the security boundary.

## Registration

- App id: `mlv_world_workspace`
- Display name: **My Little Vicinity**
- Launch type: browser / PWA workspace
- Default visibility for artifacts: **private**
- Claim status: `prototype_world_workspace`

## Bridge

`src/gunnchos_launcher/mlv_bridge.py`

```text
open_home()
open_node(node_id)
open_public_node(node_id)
open_share(token)
launch_app_for_node(node)
get_recent_nodes()
```

Deep links:

```text
gunnchos://mlv/home
gunnchos://mlv/node/<uuid>
gunnchos://mlv/public/<uuid>
gunnchos://mlv/share/<token>
```

Share tokens are validated, never logged.

## Journey presets

| Preset | Posture |
|---|---|
| Studio, Arcade, Workshop | recommended |
| Car, Laboratory, Spaceship | available |
| Offline | cached owner subset only |
| Library | public / ephemeral guest only |
| Classroom, Guardian | policy-controlled — not auto-enabled |
| Scooter, Bicycle | 3D path omitted |

Do not weaken existing guardian, classroom, or library rules.

## Artifact intent

Schema: `shared_contracts/mlv_artifact_intent.schema.json`

WAIKE (or any app) may emit `GunnchOSArtifactIntent` only with `default_visibility: "private"`. MLV places the node on the owner desk. Share/Publish is an explicit owner action.

## Honest claims

Allowed: prototype World Workspace, private-by-default contract, unlisted share links, public gallery, launcher registration.

Not claimed: production secure OS, E2EE, enterprise cloud, production MDM, perfect offline sync, malware-free uploads, production multiplayer.

## Tests

- `tests/test_mlv_bridge.py`
- `tests/test_mlv_artifact_intent_schema.py`
- existing app registry tests
