# CX1 Ordinary-User Digital Foundations

Additive product authorities under `gunnchos_device_os/cx1/`, extending CX0 scaffolds.

## Authorities

| Authority | Module | Role |
|-----------|--------|------|
| Home | `home.py` | Shell wiring all authorities |
| Vault | `vault.py` | Files, trash, backup/restore, sync queue |
| App Center | `app_center.py` | Discover/install/launch/update/remove |
| Connect | `connect.py` | Mail/calendar/contacts + local protocol fixtures |
| Assist | `assist.py` | Accessibility digital paths |
| Care | `care.py` | SupportBundle + recovery |

Also: Identity (`identity.py`), Permissions (`permissions.py`), Browser (`browser.py`),
Productivity (`productivity.py`), Printing (`printing.py`), Offline (`offline.py`),
Security (`security.py`).

## Claim boundary

- Provider-dependent paths **fail closed** (Flatpak, xdg-desktop-portal, Thunderbird, etc.).
- Physical print = `PHYSICAL_PENDING`.
- Human accessibility = `HUMAN_A11Y_PENDING` / never auto-PASS from automation.
- No Gmail/Outlook completeness claims.
- No fake TPM/secure-boot/SE PASS.
- Does **not** modify Device Lab #134, release manifests, or gate evidence.
- `FULL_COMPLETE_EXPERIENCE_COMPLETE=false`

## Evidence

`artifacts/complete_experience/cx1/`

## CLI

```bash
python -m gunnchos_device_os.cx1.cli --root /tmp/cx1 first-run --name Alex --policy School
python -m gunnchos_device_os.cx1.cli --root /tmp/cx1 journeys
python -m gunnchos_device_os.cx1.cli --root /tmp/cx1 evidence --repo-root .
```

## Tests

```bash
python -m pytest tests/cx0 tests/cx1 -q
```
