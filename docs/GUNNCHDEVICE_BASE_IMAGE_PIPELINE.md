# GUNNCHDEVICE_BASE_IMAGE_PIPELINE

Resumable sealed engineering base + COW overlays for gunnchDevice Lab.

**Multi-GB images are NEVER committed to Git.** Git tracks manifests, scripts, hashes, and stage checkpoints only.

## Flow

```
canonical engineering image (Debian cloud cache)
        │
        ▼
provision once (guest-native cloud-init / QEMU)
        │
        ▼
gunnchOS packages + tooling
        │
        ▼
guest agent
        │
        ▼
validate → GUNNCHOS_INTERACTIVE_GUEST_PROVISION_OK (boot-ready sentinel)
        │
        ▼
clean shutdown (ACPI poweroff; never hard-kill mid-write)
        │
        ▼
seal (chmod a-w + uchg) → version → SHA-256
        │
        ▼
COW overlays per persona / device  (REGENERABLE — discard OK)
```

## Commands

```bash
# Status / resume decision
python3 scripts/gunnchdevice_base_image_pipeline.py status
python3 scripts/gunnchdevice_base_image_pipeline.py safe-resume

# After sentinel PASS + clean poweroff
python3 scripts/gunnchdevice_base_image_pipeline.py seal

# Persona/device run (does not mutate sealed base)
python3 scripts/gunnchdevice_base_image_pipeline.py overlay --persona G11
export GUNNCH_LAB_OVERLAY_PERSONA=G11   # boot path auto-resolves COW

# Discard regenerable overlay only
python3 scripts/gunnchdevice_base_image_pipeline.py discard-overlay --persona G11
```

Make aliases:

```bash
make safe-halt-guest          # I need to leave now
make base-image-status
make base-image-seal
```

## SAFE_HALT — “I need to leave now”

1. Flush evidence to disk (`artifacts/product_use/`, pipeline `CHECKPOINT.json`).
2. Run:

```bash
make safe-halt-guest
# or:
python3 scripts/gunnchdevice_base_image_pipeline.py safe-halt --reason leaving_now
```

3. **Do not** `kill -9` QEMU. Prefer leave-running if mid-write; otherwise guest ACPI poweroff.
4. **Do not** delete `interactive-root-*.qcow2` or sealed manifests.
5. WiFi may disconnect; resume later via `safe-resume`.

## SAFE_RESUME

| Condition | Decision |
|-----------|----------|
| QEMU still running | `CONTINUE_RUNNING_INSTANCE` — no second QEMU |
| Sentinel PASS, image present | `PRESERVE_AND_SEAL` / `SEALED_READY_USE_COW` |
| Partial image, no sentinel | `RESUME_FROM_LAST_SAFE_STAGE` — do not delete |
| Unsafe / missing | `BLOCKED_SAFE_GUEST_RESUME` |

## Immutability

- Sealed base: read-only (+ macOS `uchg` when available).
- Boot path defaults to COW overlay (`GUNNCH_LAB_OVERLAY_PERSONA`).
- `GUNNCH_LAB_ALLOW_BASE_RW=1` is emergency-only and discouraged.
- Overlay discard is allowed **only** when `regenerable=true`.

## Package refresh without base rebuild

Use preserved sealed base + COW overlay + versioned owner package refresh.
Reject stale packages. Do **not** rebuild the sealed base solely for package updates.
