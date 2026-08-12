# Image Realm Schema (`gunnchos.image_realm.v1`)

Machine-readable realm definitions consumed by `gunnchctl os-image`
(`gunnchos_device_os/release_engineering/image_realms.py`).

Each realm file is YAML with the following top-level keys:

| Key | Type | Meaning |
|---|---|---|
| `schema` | str | Always `gunnchos.image_realm.v1` |
| `realm_id` | str | One of the five realm ids (must match filename stem, upper) |
| `status` | str | `ACTIVE_DEV` \| `ACTIVE` \| `NOT_RELEASED` |
| `description` | str | One-line human summary |
| `packages.included` / `packages.excluded` | list[str] | Package/service ids |
| `debug_access` | obj | `enabled`, `methods[]`, `requires_unlock` |
| `developer_mode` | obj | `enabled`, `unlock_policy`, `persists_across_updates` |
| `logging` | obj | `level`, `remote_upload`, `retention_days`, `redaction_required` |
| `telemetry` | obj | `enabled`, `scope`, `opt_out_supported` |
| `update_channel` | str | Update channel id this realm ships on |
| `trust_roots` | obj | `key_source` (`dev`\|`ci`\|`production`), `signing_keys[]`, `production_private_keys_present` (must be `false` everywhere in this repo), `anti_rollback_enforced` |
| `secrets_policy` | obj | `allowed_secret_classes[]`, `forbidden[]` |
| `recovery_behavior` | obj | `auto_recovery_on_boot_failure`, `recovery_partition_required`, `factory_reset_available` |
| `factory_only_services` | list[str] | Services only present in FACTORY_PROVISIONING_IMAGE |
| `production_restrictions` | obj | `shell_access`, `adb_equivalent`, `root_access`, `allow_unsigned_updates`, `debug_access_allowed` |
| `claim_boundary` | str | Honest one-paragraph claim boundary |

## Validation rules (enforced by `image_realms.validate_realm`)

1. `production_private_keys_present` must be `false` in every realm (no exceptions).
2. `PRODUCTION_SHIPPING_IMAGE_DEFINITION` must have `status: NOT_RELEASED`,
   `trust_roots.key_source: production` is **forbidden** in this repo (must be
   `none`/`dev` placeholder — real production signing happens outside this
   repository, never with keys checked in or generated here),
   `production_restrictions.debug_access_allowed: false`,
   `production_restrictions.allow_unsigned_updates: false`.
3. `RECOVERY_IMAGE` must have `recovery_behavior.recovery_partition_required: true`.
4. `FACTORY_PROVISIONING_IMAGE` must declare at least one `factory_only_services` entry.
5. `DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST` and `EVT_ENGINEERING_IMAGE` must
   have `developer_mode.enabled: true`.
