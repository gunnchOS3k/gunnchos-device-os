#!/bin/bash
# Local Flatpak repo: installable Platform runtime + CX2HTestApp v1/v2 (visually distinct).
set -uo pipefail
export FLATPAK_USER_DIR=/var/lib/cx2h/flatpak-user
REPO=/var/lib/cx2h/flatpak-repo
SRC=/var/lib/cx2h/flatpak-src
WORK=/var/lib/cx2h/flatpak-work
REMOTE=cx2h-local
ARCH=$(uname -m)
ID_RT=org.gunnchos.Platform
ID_APP=org.gunnchos.CX2HTestApp

mkdir -p "$FLATPAK_USER_DIR" "$WORK" "$SRC"
# Wipe prior user installs so stale/invalid runtime metadata cannot block app installs
rm -rf "$FLATPAK_USER_DIR" "$WORK"/* "$REPO" 2>/dev/null || true
mkdir -p "$FLATPAK_USER_DIR" "$REPO" "$WORK"
ostree --repo="$REPO" init --mode=archive-z2

echo "=== runtime bootstrap ==="
RBUILD="$WORK/rt-build"
rm -rf "$RBUILD"
# Runtimes exported via build-export require a usr/ sysroot (not files/)
mkdir -p "$RBUILD/usr/bin"
printf '%s\n' '#!/bin/sh' 'exit 0' > "$RBUILD/usr/bin/trueish"
chmod +x "$RBUILD/usr/bin/trueish"
# Also provide files/ mirror for ostree fallback consumers
mkdir -p "$RBUILD/files/bin"
cp -a "$RBUILD/usr/bin/trueish" "$RBUILD/files/bin/trueish"
cat > "$RBUILD/metadata" <<EOF
[Runtime]
name=${ID_RT}
runtime=${ID_RT}/${ARCH}/stable
sdk=${ID_RT}/${ARCH}/stable
EOF

if flatpak build-export --verbose --arch="$ARCH" --runtime --subject="${ID_RT} stable" "$REPO" "$RBUILD" stable \
  2>"$WORK/rt-export.err"; then
  echo RT_EXPORT_OK
else
  echo RT_EXPORT_FAIL
  cat "$WORK/rt-export.err"
  # Commit installable runtime tree: metadata + files/ at commit root with real newlines in xa.metadata
  RT_TREE="$WORK/rt-tree"
  rm -rf "$RT_TREE"
  mkdir -p "$RT_TREE/files"
  # Prefer usr contents under files for flatpak runtime layout fallback
  if [ -d "$RBUILD/usr" ]; then
    mkdir -p "$RT_TREE/usr"
    cp -a "$RBUILD/usr/." "$RT_TREE/usr/"
    cp -a "$RBUILD/usr/." "$RT_TREE/files/"
  else
    cp -a "$RBUILD/files/." "$RT_TREE/files/"
  fi
  cp -a "$RBUILD/metadata" "$RT_TREE/metadata"
  # Write xa.metadata via a commit modifier file (preserve newlines)
  python3 - <<PY
import gi
gi.require_version('OSTree', '1.0')
from gi.repository import OSTree, GLib
repo = OSTree.Repo.new_for_path("$REPO")
repo.open(None)
metadata = open("$RBUILD/metadata","rb").read()
# Use ostree CLI with binary metadata via flatpak build-commit-from if available
print("META_BYTES", len(metadata))
PY
  # flatpak build-commit-from can attach xa.metadata from a file
  ostree --repo="$REPO" commit \
    --branch="runtime/${ID_RT}/${ARCH}/stable" \
    --subject="${ID_RT} stable" \
    --owner-uid=0 --owner-gid=0 --no-xattrs \
    --add-metadata-string="xa.ref=runtime/${ID_RT}/${ARCH}/stable" \
    --tree=dir="$RT_TREE"
  if flatpak build-commit-from --verbose --no-update-summary \
      --base="runtime/${ID_RT}/${ARCH}/stable" \
      --subject="${ID_RT} stable" \
      --extra-metadata="$RBUILD/metadata" \
      "$REPO" "runtime/${ID_RT}/${ARCH}/stable" 2>"$WORK/rt-commit-from.err"; then
    echo RT_COMMIT_FROM_OK
  else
    echo RT_COMMIT_FROM_FAIL
    cat "$WORK/rt-commit-from.err" || true
  fi
  echo RT_OSTREE_OK
fi

flatpak build-update-repo --verbose "$REPO" 2>&1 | tail -20
ostree --repo="$REPO" refs
flatpak --user remote-delete --force "$REMOTE" 2>/dev/null || true
flatpak --user remote-add --no-gpg-verify "$REMOTE" "file://$REPO"
flatpak --user remote-ls -d "$REMOTE" 2>&1 | head -40 || true

echo "=== install runtime ==="
flatpak --user uninstall -y "$ID_RT" 2>/dev/null || true
if flatpak --user install -y --noninteractive "$REMOTE" "runtime/${ID_RT}/${ARCH}/stable" 2>&1 | tee /tmp/cx2h-rt-install.log; then
  echo RT_INSTALL_OK
else
  echo RT_INSTALL_FAIL
  cat /tmp/cx2h-rt-install.log
fi
flatpak --user info "$ID_RT" 2>&1 | head -30 || true
# Dump runtime xa.metadata for diagnosis
python3 - <<'PY' || true
import subprocess, json
r = subprocess.run(
  ["ostree", "--repo=/var/lib/cx2h/flatpak-repo", "show", "--print-metadata",
   "runtime/org.gunnchos.Platform/aarch64/stable"],
  capture_output=True, text=True)
print("RT_META_SHOW:")
print((r.stdout or r.stderr or "")[:2000])
PY

write_launcher() {
  local DEST="$1" VER="$2"
  cat > "$DEST" <<EOF
#!/bin/sh
export VERSION=$VER
HTML=/app/share/cx2h-testapp/index.html
CHROMIUM=""
for c in /run/host/usr/bin/chromium /run/host/usr/bin/chromium-browser /usr/bin/chromium /usr/bin/chromium-browser; do
  [ -x "\$c" ] && CHROMIUM="\$c" && break
done
[ -n "\$CHROMIUM" ] || { echo NO_CHROMIUM; exit 1; }
exec "\$CHROMIUM" --ozone-platform=wayland --user-data-dir=/var/tmp/cx2h-testapp-\$VERSION \
  --no-first-run --disable-sync --app="file://\$HTML"
EOF
  chmod +x "$DEST"
}

build_app() {
  local VER="$1" SRCVER="$2" BRANCH="$3"
  local ABUILD="$WORK/app-${SRCVER}-${BRANCH}"
  echo "=== app $VER /$BRANCH ==="
  rm -rf "$ABUILD"

  if flatpak build-init --arch="$ARCH" "$ABUILD" "$ID_APP" "$ID_RT" "$ID_RT" stable 2>"$WORK/init-${BRANCH}.err"; then
    echo APP_INIT_OK_$BRANCH
  else
    echo APP_INIT_FAIL_$BRANCH
    cat "$WORK/init-${BRANCH}.err"
    mkdir -p "$ABUILD/files"
    cat > "$ABUILD/metadata" <<EOF
[Application]
name=${ID_APP}
runtime=${ID_RT}/${ARCH}/stable
sdk=${ID_RT}/${ARCH}/stable
command=cx2h-testapp
EOF
  fi

  mkdir -p "$ABUILD/files/bin" "$ABUILD/files/share/cx2h-testapp"
  cp -a "$SRC/app-$SRCVER/share/." "$ABUILD/files/share/cx2h-testapp/"
  write_launcher "$ABUILD/files/bin/cx2h-testapp" "$VER"

  if flatpak build-finish \
      --command=cx2h-testapp \
      --share=ipc \
      --socket=wayland --socket=x11 \
      --device=dri \
      --filesystem=host-os \
      --filesystem=/var/tmp \
      --env=VERSION="$VER" \
      "$ABUILD" 2>"$WORK/finish-${BRANCH}.err"; then
    echo APP_FINISH_OK_$BRANCH
  else
    echo APP_FINISH_FAIL_$BRANCH
    cat "$WORK/finish-${BRANCH}.err"
    cat > "$ABUILD/metadata" <<EOF
[Application]
name=${ID_APP}
runtime=${ID_RT}/${ARCH}/stable
sdk=${ID_RT}/${ARCH}/stable
command=cx2h-testapp

[Context]
shared=ipc;
sockets=wayland;x11;
devices=dri;
filesystems=host-os;/var/tmp;

[Environment]
VERSION=$VER
EOF
    mkdir -p "$ABUILD/export/share/applications"
    cat > "$ABUILD/export/share/applications/${ID_APP}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=CX2H Test App
Exec=cx2h-testapp
Terminal=false
EOF
  fi

  if flatpak build-export --verbose --arch="$ARCH" --subject="CX2HTestApp $VER" "$REPO" "$ABUILD" "$BRANCH" \
      2>"$WORK/ex-${BRANCH}.err"; then
    echo APP_EXPORT_OK_$BRANCH
  else
    echo APP_EXPORT_FAIL_$BRANCH
    cat "$WORK/ex-${BRANCH}.err"
    exit 1
  fi

  flatpak build-update-repo --generate-static-deltas "$REPO" >/dev/null 2>&1 || flatpak build-update-repo "$REPO" >/dev/null 2>&1 || true
  flatpak --user uninstall -y "$ID_APP" 2>/dev/null || true
  if flatpak --user install -y --noninteractive "$REMOTE" "app/${ID_APP}/${ARCH}/${BRANCH}" \
      2>"$WORK/inst-${BRANCH}.err"; then
    echo APP_INSTALL_OK_$BRANCH
    flatpak --user info "$ID_APP" 2>&1 | head -25 || true
  else
    echo APP_INSTALL_FAIL_$BRANCH
    cat "$WORK/inst-${BRANCH}.err"
  fi
}

build_app 1.0.0 v1 1.0.0
build_app 1.0.0 v1 stable
build_app 2.0.0 v2 2.0.0
flatpak build-update-repo --verbose "$REPO" 2>&1 | tail -20

flatpak --user remote-delete --force "$REMOTE" 2>/dev/null || true
flatpak --user remote-add --no-gpg-verify "$REMOTE" "file://$REPO"
flatpak --user uninstall -y "$ID_APP" 2>/dev/null || true

echo "=== FINAL remote-ls ==="
flatpak --user remote-ls -d "$REMOTE" 2>&1 || true
echo "=== FINAL refs ==="
ostree --repo="$REPO" refs || true

: > /tmp/cx2h-flatpak-installable.marker
for B in 1.0.0 2.0.0 stable; do
  flatpak --user uninstall -y "$ID_APP" 2>/dev/null || true
  if flatpak --user install -y --noninteractive "$REMOTE" "app/${ID_APP}/${ARCH}/$B" 2>/tmp/cx2h-verify-$B.err; then
    echo VERIFY_INSTALL_OK_$B
    echo "$B" >> /tmp/cx2h-flatpak-installable.marker
    flatpak --user run --command=true "$ID_APP" 2>/dev/null || true
    flatpak --user uninstall -y "$ID_APP" 2>/dev/null || true
  else
    echo VERIFY_INSTALL_FAIL_$B
    cat /tmp/cx2h-verify-$B.err || true
  fi
done

if ostree --repo="$REPO" refs | grep -q "app/${ID_APP}/" && [ -s /tmp/cx2h-flatpak-installable.marker ]; then
  echo FLATPAK_REPO_BUILT
  exit 0
fi
echo FLATPAK_REPO_MISSING_APP_REFS
exit 1
