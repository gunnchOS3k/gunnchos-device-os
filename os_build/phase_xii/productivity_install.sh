#!/usr/bin/env bash
# Install real productivity stack into a Debian/Ubuntu rootfs or CI runner.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  chromium firefox-esr \
  libreoffice-writer libreoffice-calc libreoffice-impress libreoffice-draw \
  evince \
  nautilus \
  gnome-terminal \
  code || true
apt-get install -y --no-install-recommends \
  git ffmpeg mpv cups cups-client wireguard-tools openvpn \
  weston xvfb xdotool at-spi2-core \
  python3 python3-pip
echo "gunnchOS productivity install complete"
