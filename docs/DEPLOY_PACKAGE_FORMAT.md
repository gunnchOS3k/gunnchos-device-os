# Deploy Package Format

**Status:** device OS alpha · logical package types (no binary spec yet)  
**Config:** `config/deploy_targets.yaml` → `package_types`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Package type catalog

| Package type | Description | Typical contents (alpha) | Example targets |
|--------------|-------------|--------------------------|-----------------|
| `web_app` | Static or Vite-built web project | HTML, JS, assets folder | student_14_5, handheld_hybrid, classroom |
| `python_project` | Python lesson or script bundle | `.py`, `requirements.txt`, README | student_14_5, ds_xl_local_preview |
| `game_project` | Game jam export | Project JSON, assets | handheld_hybrid, ds_xl_local_preview |
| `lesson_pack` | WAIKE/offline lesson bundle | YAML/JSON lesson manifest | All except ds_xl-only edge tasks |
| `media_project` | Creative media stub | Placeholder media files | student, handheld, classroom |
| `edge_measurement_task` | Edge-IO field task definition | Task YAML, consent manifest | ds_xl_local_preview only |
| `research_notebook` | Research notes export | Markdown, CSV exports | student_14_5, ds_xl_local_preview |

---

## Logical bundle structure (placeholder)

Future signed bundles may follow:

```
gunnchos-package/
├── manifest.json          # package_type, version, source, target_class
├── consent.json           # user_consent timestamp (placeholder)
├── signature.placeholder  # future Ed25519 / CMS signature
├── payload/               # project files
└── rollback.json          # rollback instructions placeholder
```

**Alpha:** No on-disk format is produced — `deploy_package()` returns JSON status only.

---

## manifest.json (planned fields)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `package_type` | string | Yes | One of global package_types |
| `source_device` | string | Yes | e.g. `ds_xl_coder` |
| `target_device_class` | string | Yes | e.g. `student_14_5` |
| `created_at` | ISO8601 | Yes | Build timestamp |
| `no_private_data` | bool | Yes | Must be true for school targets |
| `mock` | bool | Yes | True in alpha builds |

---

## Transport-specific packaging

| Transport | Bundle wrapper |
|-----------|----------------|
| `local_wifi` | Network transfer of signed bundle (future) |
| `usb_c` | Same bundle over USB MTP/adb-class protocol (future) |
| `offline_export_bundle` | ZIP with manifest + signature placeholder |
| `local_folder_export` | Unwrapped folder tree |
| `qr_pairing_placeholder` | QR encodes pairing token + bundle URL (future) |

---

## Size and content rules (policy)

1. No keystroke logs, message content, or private packet captures in any package type
2. `lesson_pack` must declare `offline_capable: true|false`
3. `edge_measurement_task` must include consent manifest referencing `edge_io_contract.yaml`
4. Shared classroom targets should avoid user-specific paths in payload

---

## WAIKE lesson deploy

`waike_integration.deploy_lesson()` returns a separate mock dict — lesson packs may be referenced by deploy but are not unified into binary format yet.

---

## Related documents

- [DS_XL_DEPLOY_CONTRACT.md](DS_XL_DEPLOY_CONTRACT.md)
- [DEPLOY_FAILURE_MODES.md](DEPLOY_FAILURE_MODES.md)
- [DEPLOY_ROLLBACK_MODEL.md](DEPLOY_ROLLBACK_MODEL.md)
