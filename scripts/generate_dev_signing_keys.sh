#!/usr/bin/env bash
# Generate development signing keys for release manifest smoke tests.
# NOT production keys — see security/secure_boot/CLAIM_BOUNDARY.md
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KEY_DIR="$ROOT/security/secure_boot/dev_keys"
mkdir -p "$KEY_DIR"
PRIV="$KEY_DIR/image_signing_dev.pem"
PUB="$KEY_DIR/image_signing_dev.pub.pem"

if [[ -f "$PRIV" ]]; then
  echo "Dev keys already exist at $KEY_DIR (delete to regenerate)"
  exit 0
fi

openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$PRIV"
openssl rsa -in "$PRIV" -pubout -out "$PUB"
chmod 600 "$PRIV"
echo "Generated dev signing keys:"
echo "  private: $PRIV"
echo "  public:  $PUB"
