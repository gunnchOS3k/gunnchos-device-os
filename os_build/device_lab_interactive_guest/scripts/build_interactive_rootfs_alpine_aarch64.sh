#!/usr/bin/env bash
# gunnchOS Device Lab Interactive Development Guest — real Alpine aarch64
# rootfs build (weston + terminal + guest agent hooks).
#
# HONESTY CONTRACT: this script performs *real* steps when tools are
# available (real network fetch, real docker/chroot package install, real
# qemu-img disk allocation). When a required capability is missing on the
# host, it prints the exact missing capability and exits non-zero. It never
# fabricates success, never writes a fake "PASS" evidence file, and never
# claims a boot or GUI result it did not actually produce.
#
# DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST=true. SHIPPING_IMAGE=false.
# SILICON_EXACT_EMULATION=false. This guest is never a shipping image.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCH="aarch64"
ALPINE_MAJOR_MINOR="3.21"
ALPINE_VERSION="3.21.3"
ALPINE_MIRROR="https://dl-cdn.alpinelinux.org/alpine/v${ALPINE_MAJOR_MINOR}/releases/${ARCH}"

REPO_ROOT=""
SIZE_GB=8
DRY_RUN=0

REQUIRED_PACKAGES=(alpine-baselayout busybox seatd weston mesa-dri-gallium foot chromium nano pipewire pipewire-alsa libinput godot)
REQUIRED_PACKAGES_NO_OPTIONAL=(alpine-baselayout busybox seatd weston mesa-dri-gallium foot chromium nano pipewire pipewire-alsa libinput)

usage() {
  cat <<'EOF'
Usage: build_interactive_rootfs_alpine_aarch64.sh [--repo-root PATH] [--size-gb N] [--dry-run]

Builds a real Alpine aarch64 rootfs with weston + terminal + guest agent
hooks for the gunnchOS Device Lab Interactive Development Guest.

Exit codes:
  0  rootfs materialized (packages actually installed with real scripts run)
  1  honest failure — see stderr + INTERACTIVE_ROOTFS_BUILD_EVIDENCE.json
  64 usage error
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root) REPO_ROOT="$2"; shift 2 ;;
    --size-gb) SIZE_GB="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage; exit 64 ;;
  esac
done

if [[ -z "$REPO_ROOT" ]]; then
  REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
fi

INTERACTIVE_ROOT="$REPO_ROOT/os_build/device_lab_interactive_guest"
CACHE_DIR="$INTERACTIVE_ROOT/cache"
WORK_DIR="$INTERACTIVE_ROOT/work"
ARTIFACTS_DIR="$INTERACTIVE_ROOT/artifacts"
OVERLAY_DIR="$INTERACTIVE_ROOT/overlay"
ROOTFS_DIR="$WORK_DIR/rootfs"
DISK_PATH="$ARTIFACTS_DIR/interactive-root-${ARCH}.qcow2"
EVIDENCE_PATH="$ARTIFACTS_DIR/INTERACTIVE_ROOTFS_BUILD_EVIDENCE.json"
MINIROOTFS_TAR="$CACHE_DIR/alpine-minirootfs-${ALPINE_VERSION}-${ARCH}.tar.gz"

mkdir -p "$CACHE_DIR" "$WORK_DIR" "$ARTIFACTS_DIR"

log() { echo "[interactive-rootfs] $*" >&2; }

write_evidence() {
  # $1 = ok (true/false), $2 = reason, $3 = method, $4 = extra json fields (raw, no braces)
  local ok="$1" reason="$2" method="$3" extra="${4:-}"
  local extra_json=""
  if [[ -n "$extra" ]]; then
    extra_json=",${extra}"
  fi
  cat > "$EVIDENCE_PATH" <<EOF
{
  "schema": "gunnchos.device_lab.interactive_guest_rootfs_build_evidence.v1",
  "ok": ${ok},
  "arch": "${ARCH}",
  "method": "${method}",
  "reason": "${reason}",
  "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": true,
  "SHIPPING_IMAGE": false,
  "SILICON_EXACT_EMULATION": false,
  "production_keys_used": false,
  "physical_boot_claimed": false,
  "alpine_version": "${ALPINE_VERSION}",
  "host_system": "$(uname -s)",
  "host_machine": "$(uname -m)"${extra_json}
}
EOF
}

fail_honest() {
  local reason="$1" method="${2:-none}"
  log "FAIL (honest, non-zero exit): $reason"
  write_evidence false "$reason" "$method"
  exit 1
}

require_tool() {
  command -v "$1" >/dev/null 2>&1 || fail_honest "required_tool_missing:$1" "none"
}

require_tool curl
require_tool tar

QEMU_IMG="$(command -v qemu-img || true)"
if [[ -z "$QEMU_IMG" && -x /opt/homebrew/bin/qemu-img ]]; then
  QEMU_IMG="/opt/homebrew/bin/qemu-img"
fi
[[ -n "$QEMU_IMG" ]] || fail_honest "required_tool_missing:qemu-img" "none"

log "Fetching real Alpine ${ALPINE_VERSION} ${ARCH} minirootfs (network required)..."
if [[ ! -s "$MINIROOTFS_TAR" ]]; then
  if ! curl -fsSL -o "$MINIROOTFS_TAR" "${ALPINE_MIRROR}/alpine-minirootfs-${ALPINE_VERSION}-${ARCH}.tar.gz"; then
    rm -f "$MINIROOTFS_TAR"
    fail_honest "alpine_minirootfs_fetch_failed" "none"
  fi
fi
log "minirootfs cached: $MINIROOTFS_TAR ($(wc -c < "$MINIROOTFS_TAR") bytes)"

if [[ "$DRY_RUN" == "1" ]]; then
  log "dry-run requested; stopping after real network fetch (no package install attempted)"
  write_evidence true "dry_run_fetch_only" "dry_run" "\"dry_run\": true, \"packages_installed\": false"
  exit 0
fi

# --- Detect real cross-build capability (never assume) -----------------
METHOD="none"
DOCKER_BIN="$(command -v docker || true)"
if [[ -n "$DOCKER_BIN" ]] && "$DOCKER_BIN" info >/dev/null 2>&1; then
  METHOD="docker"
elif [[ "$(uname -s)" == "Linux" ]] && [[ -d /proc/sys/fs/binfmt_misc ]] \
     && { command -v qemu-aarch64-static >/dev/null 2>&1 || command -v qemu-aarch64 >/dev/null 2>&1; } \
     && command -v chroot >/dev/null 2>&1; then
  METHOD="chroot_binfmt"
fi

if [[ "$METHOD" == "none" ]]; then
  fail_honest \
    "no_real_cross_build_method_available: apk post-install trigger scripts must execute real aarch64 Linux binaries; need docker (native linux/arm64 on Apple Silicon) or a Linux host with binfmt_misc+qemu-user-static. Neither found on this host ($(uname -s) $(uname -m)). Real minirootfs was fetched (see cache) but package install was NOT attempted, and NO fake PASS is recorded." \
    "none"
fi

log "Using real build method: $METHOD"
mkdir -p "$ROOTFS_DIR"
GODOT_INSTALLED=false

if [[ "$METHOD" == "docker" ]]; then
  DOCKER_ARCH="arm64"
  [[ "$ARCH" == "x86_64" ]] && DOCKER_ARCH="amd64"
  log "docker run --platform linux/${DOCKER_ARCH} alpine:${ALPINE_MAJOR_MINOR} apk add --root /target ..."
  if "$DOCKER_BIN" run --rm --platform "linux/${DOCKER_ARCH}" \
      -v "$ROOTFS_DIR":/target \
      "alpine:${ALPINE_MAJOR_MINOR}" \
      sh -c "set -e; apk update; apk add --root /target --initdb -U --allow-untrusted ${REQUIRED_PACKAGES[*]}"; then
    GODOT_INSTALLED=true
  else
    log "full package set (incl. optional godot) failed; retrying without optional godot"
    if "$DOCKER_BIN" run --rm --platform "linux/${DOCKER_ARCH}" \
        -v "$ROOTFS_DIR":/target \
        "alpine:${ALPINE_MAJOR_MINOR}" \
        sh -c "set -e; apk update; apk add --root /target --initdb -U --allow-untrusted ${REQUIRED_PACKAGES_NO_OPTIONAL[*]}"; then
      GODOT_INSTALLED=false
    else
      fail_honest "docker_apk_add_failed_even_without_optional_godot" "docker"
    fi
  fi
elif [[ "$METHOD" == "chroot_binfmt" ]]; then
  [[ "$(id -u)" == "0" ]] || fail_honest "chroot_binfmt_requires_root" "chroot_binfmt"
  tar -xzf "$MINIROOTFS_TAR" -C "$ROOTFS_DIR"
  QEMU_USER="$(command -v qemu-aarch64-static || command -v qemu-aarch64)"
  cp "$QEMU_USER" "$ROOTFS_DIR/usr/bin/qemu-aarch64-static"
  if chroot "$ROOTFS_DIR" /usr/bin/qemu-aarch64-static /sbin/apk add --initdb -U --allow-untrusted "${REQUIRED_PACKAGES[@]}"; then
    GODOT_INSTALLED=true
  else
    log "full package set (incl. optional godot) failed; retrying without optional godot"
    if chroot "$ROOTFS_DIR" /usr/bin/qemu-aarch64-static /sbin/apk add --initdb -U --allow-untrusted "${REQUIRED_PACKAGES_NO_OPTIONAL[@]}"; then
      GODOT_INSTALLED=false
    else
      fail_honest "chroot_apk_add_failed_even_without_optional_godot" "chroot_binfmt"
    fi
  fi
fi

# --- Copy overlay (first-boot weston + guest agent hooks) --------------
if [[ -d "$OVERLAY_DIR" ]]; then
  log "copying overlay/ (first-boot weston + guest agent hooks) into rootfs"
  cp -a "$OVERLAY_DIR"/. "$ROOTFS_DIR"/
fi

# --- Real qcow2 root disk placeholder (allocation only) ----------------
if [[ ! -s "$DISK_PATH" ]]; then
  "$QEMU_IMG" create -f qcow2 "$DISK_PATH" "${SIZE_GB}G" >/dev/null
fi
log "qcow2 root disk placeholder: $DISK_PATH (${SIZE_GB}G, filesystem NOT yet written — see README)"

WESTON_PRESENT=false
[[ -x "$ROOTFS_DIR/usr/bin/weston" ]] && WESTON_PRESENT=true

write_evidence true "rootfs_materialized" "$METHOD" "\
\"packages_installed\": true, \
\"godot_installed\": ${GODOT_INSTALLED}, \
\"weston_binary_present\": ${WESTON_PRESENT}, \
\"disk_path\": \"${DISK_PATH}\", \
\"disk_formatted\": false, \
\"rootfs_packed_onto_disk\": false, \
\"note\": \"Packages installed into ${ROOTFS_DIR} via ${METHOD}; rootfs not yet packed onto the qcow2 disk (requires mkfs + copy, not yet automated in this script version). No boot attempted by this script.\""

log "Rootfs materialized at $ROOTFS_DIR via $METHOD. weston_binary_present=$WESTON_PRESENT godot_installed=$GODOT_INSTALLED"
log "NOTE: rootfs is NOT yet packed onto $DISK_PATH — that step is documented but not automated here. No PASS token is implied by this script."
exit 0
