# Deploy Rollback Model

**Status:** device OS alpha · placeholder rollback path  
**Module:** `gunnchos_device_os/deploy_contract.py`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Rollback path (alpha)

Successful deploy returns:

```python
"rollback_path": "delete_package_or_rollback_placeholder"
```

No automatic rollback executes in alpha — field documents **intended** behavior.

---

## Rollback triggers (planned)

| Trigger | Actor | Action |
|---------|-------|--------|
| User undo | Student | "Remove package" within 24h window |
| Guardian revoke | Guardian | Remove unapproved app/package |
| Admin push | Fleet admin | Remote remove (future MDM) |
| Signature failure on update | System | Block install; keep previous version |
| Developer mode reset | Developer | `rollback_safe_reset` in Developer mode policy |

---

## Rollback scope

| Package type | Rollback behavior (planned) |
|--------------|----------------------------|
| web_app | Delete deployed folder; restore previous static snapshot |
| python_project | Remove venv + project copy |
| lesson_pack | Revert lesson manifest version |
| game_project | Remove build artifact |
| edge_measurement_task | Delete task + local exports |
| research_notebook | Archive notebook; keep user-owned notes |

---

## Data preservation

- User-created work inside package → prompt before delete
- Shared classroom device → no personal data assumed
- Research exports → user may keep CSV/JSON per Edge-IO contract

---

## Developer mode alignment

Developer mode includes `rollback_safe_reset: true` — factory-reset-style recovery for dev workstations (planned).

Cross-link: [UPDATE_AND_ROLLBACK_MODEL.md](UPDATE_AND_ROLLBACK_MODEL.md) for OS updates (separate from package deploy).

---

## Failure: rollback incomplete (future)

Planned user message: "Rollback incomplete — see guardian or admin."

Not implemented in alpha.

---

## Testing

Deploy success mock includes rollback_path key — verify in:

```bash
PYTHONPATH=. pytest tests/test_deploy_contract.py
```

---

## Claim boundary

Rollback is **documented intent** — not a verified uninstall pipeline on hardware.
