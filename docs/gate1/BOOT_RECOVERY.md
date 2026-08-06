# Boot Recovery Instructions

## Quick recovery map

| Failure | Recovery |
|---|---|
| Missing service | Restore unit listed in manifest `services[]`; re-run probe |
| Corrupted manifest | Replace with `config/boot/sample_manifest.json`; validate schema |
| Stale image | Rebuild image; refresh `image_id` / `created_at` |
| Unsupported arch | Match `image_arch` to host or use compatible VM |
| Failed health check | Fix unhealthy service; re-run with `--failure-mode none` |
| Storage insufficient | Free space above `storage.min_free_mb` |
| Network unhealthy | Fix local hostname/loopback (no internet required) |

## Commands

```bash
python -m gunnchos_device_os.boot --recovery
python -m gunnchos_device_os.boot --failure-mode missing_service
python -m gunnchos_device_os.boot --manifest config/boot/sample_manifest.json
```

## Claim boundary

Keep `GUNNCHOS_PHYSICAL_BOOT_PENDING` until a filled physical capture from a real target is reviewed.
