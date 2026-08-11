"""WP-013 — gunnchOS Release Engineering + Developer Platform.

Real, working implementations for:
  * Image realms (os_build/image_realms/*.yaml)
  * gunnchctl os-image build|inspect|verify
  * A/B update + rollback + anti-rollback + recovery architecture
  * gunnchSDK (manifest, .gunnchpkg packaging, install/run/uninstall)
  * API compatibility gate
  * Factory provisioning digital tooling (DEV/TEST identities only)
  * Recovery / serviceability tooling

No production keys or production credentials are used anywhere in this
package. Production realm artifacts remain unsigned / NOT_RELEASED.
"""
