# FULL PRODUCT CONTINUATION VII — real first-party app/game packages

## Defect closed

PR #64 shipped `games/beatlink-party-web` as a DEV HTML stub with
`GUNNCHOS_GAME_STUB_CONTENT=true`. Cont VII forbids `STUB_AS_PRODUCT`.

## Beat Link package

| Field | Value |
|-------|-------|
| Source repo | `beatlink-party` (`gunnchOS3k/beatlink-party`) |
| Accepted SHA | `9948646870cd2caa9c85ae2796b40292d7343d88` (Cont VI #14+#15) |
| Build command | `pnpm -r build` |
| Artifact | `apps/web/dist` (+ server dist + compose) |
| Import path | `games/beatlink-party-web` |
| Manifest | `packages/first_party_games/beatlink-party/PACKAGE_MANIFEST.json` |
| Permissions | files_read, network, microphone |
| Device roles | student, handheld, ds_xl, dock_host |

Re-import:

```bash
python3 scripts/import_first_party_packages.py --beatlink-only
```

## First-party apps (mock retirement)

| App | Path | Replaces |
|-----|------|----------|
| WAIKE Learning | `apps/waike_learning` | waike stub launch-only |
| Creator / Coder Studio | `apps/creator_studio` | creator_studio → launcher_mock |
| Device Management | `apps/device_management` | `device_dashboard_mock` |

`apps/launcher_mock` remains the launcher shell UX (not a stand-in for Creator Studio).

## IPC (§26)

Host AF_UNIX JSON-line IPC is **kept** after robustness audit
(`gunnchos_device_os/ipc_robustness.py`). Guest minirootfs mailbox is an
embedded constraint, not a false digital platform blocker.

## Platform token (§27)

`FULL_GUNNCHOS_PLATFORM_DIGITAL_COMPLETE` is evaluated by
`gunnchos_device_os/platform_digital.py`.

**Not blockers:** physical boot pending, production cloud credentials, carrier attach.

## Commands

```bash
make full-product-vii
```
