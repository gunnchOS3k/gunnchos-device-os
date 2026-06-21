# Developer Mode

**Status:** device OS alpha · policy definition in `config/modes.yaml`  
**Module:** `gunnchos_device_os/mode_manager.py`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Purpose

**Developer** mode enables coding workflows on gunnchOS: VS Code, terminal, WSL Ubuntu path, git placeholder, local project folders, with rollback-safe reset.

Primary device class: **ds_xl_coder** (also available on student_14_5 and handheld_hybrid per device class config).

---

## Policy summary

| Key | Value |
|-----|-------|
| `allowed_apps` | vscode, terminal, wsl_ubuntu, browser, gunnchai3k, git_placeholder |
| `blocked_apps` | steam |
| `telemetry` | aggregated_opt_in |
| `network` | standard |
| `update` | user_prompt |
| `child_safety` | standard |
| `performance` | balanced |
| `wsl_path` | true |
| `git_github_path` | true |
| `local_project_folders` | true |
| `package_dependency_warning` | true |
| `advanced_settings` | true |
| `rollback_safe_reset` | true |

---

## DS-XL deploy source

Developer workstations on DS-XL build packages deployed to student targets — see [DS_XL_DEPLOY_CONTRACT.md](DS_XL_DEPLOY_CONTRACT.md).

---

## Transition rules

| From profile | To Developer | Requirement |
|--------------|--------------|-------------|
| child / pre_k / elementary / middle_school | Developer | Guardian approval |
| School / Library / Guardian | Developer | Explicit consent |
| adult | Developer | Allowed (telemetry may need consent) |

Telemetry rule: Developer is in `telemetry_requires_consent.modes_requiring_consent` — consent may block telemetry until given.

---

## Related modes

| Mode | Relationship |
|------|--------------|
| **Coder** | Subset — coding without full WSL/advanced settings emphasis |
| **Workshop** | Maker/hardware lab focus |
| **Admin** | Superset privileges — blocked from School without consent |

---

## Edge cases

`edge_case_policy.py` includes `wsl_unavailable` — Developer mode should degrade gracefully (documented in edge case requirements).

---

## Test evidence

```bash
PYTHONPATH=. pytest tests/test_modes.py::test_developer_mode
PYTHONPATH=. pytest tests/test_mode_policy.py::test_child_blocked_without_guardian
```

---

## Claim boundary

Developer mode documents **WSL-compatible strategy** — not guaranteed WSL on all hardware. Steam remains blocked; not a gaming bypass mode.
