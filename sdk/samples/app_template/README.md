# App template

Minimal adopter app skeleton for gunnchOS.

```json
{
  "schema": "gunnchos.app_manifest.v1",
  "id": "example.adopter.app",
  "version": "0.1.0",
  "api": { "app_manifest": "1.2.0", "permissions": "1.1.0" },
  "permissions": ["files_read", "network"],
  "device_roles": ["student", "office"],
  "offline": true
}
```

Build/test/package from repo root:

```bash
make bootstrap
make test
make package
```
