# Local Deploy Security Model

**Status:** device OS alpha · policy stubs for DS-XL → device transfer  
**Module:** `gunnchos_device_os/deploy_contract.py`  
**Config:** `config/deploy_targets.yaml` → `transport_methods.*.safety_policy`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Security goals

1. **No silent deploy** — user must acknowledge every transfer
2. **No private data by default** — packages exclude message content, keystrokes, private payloads
3. **Guardian gate for youth targets** — child/school devices require guardian approval when `guardian_restrictions: true`
4. **Target trust prompt** — Wi-Fi/USB/QR transports require explicit target confirmation (placeholder UX)
5. **Signed bundle path** — planning hook for future code signing (`signed_bundle_placeholder: true`)

---

## Safety policy schema

Each transport in `config/deploy_targets.yaml` includes:

```yaml
safety_policy:
  requires_user_consent: true
  requires_target_trust_prompt: true|false
  guardian_approval_for_child: true
  no_silent_deploy: true
  no_private_data_default: true
  signed_bundle_placeholder: true|false
```

Enforced in `deploy_package()`:

| Check | Condition | Failure `next_action` |
|-------|-----------|----------------------|
| Package type allow list | `package_type ∉ target.allowed_package_types` | `choose_allowed_package_type` |
| Transport allow list | `transport ∉ target.allowed_transports` | `choose_allowed_transport` |
| User consent | `requires_user_consent` and not `user_consent` | `request_user_consent` |
| Guardian approval | `guardian_restrictions` and not `guardian_approved` | `request_guardian_approval` |

---

## Threat considerations (alpha)

| Threat | Mitigation (alpha) | Production gap |
|--------|-------------------|----------------|
| Drive-by deploy on school Wi-Fi | Consent + trust prompt flags | Network ACL + mTLS |
| Malicious package on USB | Signed bundle placeholder | Real signature verification |
| Child receives game on school device | Guardian + school restriction flags | MDM enforcement |
| Data exfiltration in package | `no_private_data_default` policy | Package scanner |
| Replay of old bundle | Not addressed | Nonce + timestamp signing |

See [THREAT_MODEL.md](THREAT_MODEL.md) for broader device OS threats.

---

## Target restriction matrix

| Target | Guardian required | School restrictions | Typical use |
|--------|-------------------|---------------------|-------------|
| student_14_5 | Yes | Yes | 1:1 student laptop |
| handheld_hybrid | Yes | Yes | Personal hybrid |
| ds_xl_local_preview | No | No | Developer self-test |
| classroom_library_shared | Yes | Yes | Shared kiosk |
| wearables_arena_placeholder | Yes | Yes | Future arena kits |

---

## Safe fallback

On failure, `deploy_package()` sets:

```python
"safe_fallback": "local_folder_export"
```

User can export to a local folder without network pairing — still requires consent when policy demands it.

---

## Integration with modes and guardian

| System | Interaction |
|--------|-------------|
| `guardian_policy.py` | Approve deploy for youth profiles (conceptual; deploy uses boolean flag) |
| `mode_policy.py` | School/Library modes may block admin/developer — deploy is separate path |
| `privacy_security_model.py` | No private payload in packages aligns with data minimization |

---

## Validation

```bash
PYTHONPATH=. pytest tests/test_deploy_contract.py
python scripts/run_deploy_contract_demo.py
```

---

## Claim boundary

This model describes **intended security properties** for local deploy. It is **not** a penetration-tested production transport layer.
