# MLV integration gates

Machine-readable copy: `artifacts/mlv/MLV_INTEGRATION_GATES.json`

```text
MLV_APP_REGISTERED_PASS=true
MLV_PRIVATE_DEFAULT_SCHEMA_PASS=true
MLV_SHARE_TOKEN_REDACTION_PASS=true
MLV_DEEPLINK_VALIDATION_PASS=true
MLV_JOURNEY_PRESET_POLICY_PASS=true
MLV_HOSTED_SUPABASE_PASS=false
MLV_PIXEL_PHYSICAL_PASS=false
MLV_MERGE_AUTHORIZED=false
```

Local pytest on this branch is not hosted journey proof and not Pixel proof.
Do not merge before 3k MLV PR #1 is accepted.

```text
MERGE_ORDER:
1. 3k MLV PR #1
2. gunnchOS PR #165
```
