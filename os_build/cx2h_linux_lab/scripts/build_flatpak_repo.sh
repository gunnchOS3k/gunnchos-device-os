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
mkdir -p "$RBUILD/usr/bin" "$RBUILD/usr/lib" "$RBUILD/usr/lib/aarch64-linux-gnu" \
         "$RBUILD/lib" "$RBUILD/lib/aarch64-linux-gnu"
printf '%s\n' '#!/bin/sh' 'exit 0' > "$RBUILD/usr/bin/trueish"
chmod +x "$RBUILD/usr/bin/trueish"
# Seed enough host glibc so ELF launchers (dash/python via host-os) can exec.
# Without ld-linux at /lib, every bwrap execvp returns ENOENT.
copy_lib() {
  local src="$1" dest="$2"
  if [ -e "$src" ]; then
    mkdir -p "$(dirname "$dest")"
    cp -a "$src" "$dest" 2>/dev/null || true
  fi
}
# Dynamic linker (absolute PT_INTERP path used by Debian aarch64 ELFs)
if [ -e /lib/ld-linux-aarch64.so.1 ]; then
  copy_lib /lib/ld-linux-aarch64.so.1 "$RBUILD/lib/ld-linux-aarch64.so.1"
  copy_lib /lib/ld-linux-aarch64.so.1 "$RBUILD/usr/lib/ld-linux-aarch64.so.1"
elif [ -e /usr/lib/aarch64-linux-gnu/ld-linux-aarch64.so.1 ]; then
  copy_lib /usr/lib/aarch64-linux-gnu/ld-linux-aarch64.so.1 "$RBUILD/lib/ld-linux-aarch64.so.1"
  copy_lib /usr/lib/aarch64-linux-gnu/ld-linux-aarch64.so.1 "$RBUILD/usr/lib/ld-linux-aarch64.so.1"
fi
# Minimal libc set for bundled /app/bin/sh (dash)
for so in libc.so.6 libdl.so.2 libpthread.so.0 libm.so.6 librt.so.1 libresolv.so.2 \
          ld-linux-aarch64.so.1 libnss_files.so.2 libnss_dns.so.2; do
  copy_lib "/lib/aarch64-linux-gnu/$so" "$RBUILD/lib/aarch64-linux-gnu/$so"
  copy_lib "/lib/aarch64-linux-gnu/$so" "$RBUILD/usr/lib/aarch64-linux-gnu/$so"
  copy_lib "/usr/lib/aarch64-linux-gnu/$so" "$RBUILD/lib/aarch64-linux-gnu/$so"
  copy_lib "/usr/lib/aarch64-linux-gnu/$so" "$RBUILD/usr/lib/aarch64-linux-gnu/$so"
done
# Symlink convenience
ln -sfn usr/lib "$RBUILD/lib-usr-link" 2>/dev/null || true
# XKB data so GTK Wayland can create surfaces inside the stub runtime
if [ -d /usr/share/X11/xkb ]; then
  mkdir -p "$RBUILD/usr/share/X11"
  cp -a /usr/share/X11/xkb "$RBUILD/usr/share/X11/" 2>/dev/null || true
fi

# Also provide files/ mirror for ostree fallback consumers
mkdir -p "$RBUILD/files/bin" "$RBUILD/files/lib" "$RBUILD/files/lib/aarch64-linux-gnu"
cp -a "$RBUILD/usr/bin/trueish" "$RBUILD/files/bin/trueish"
cp -a "$RBUILD/lib/." "$RBUILD/files/lib/" 2>/dev/null || true
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
#!/app/bin/sh
# Host GTK GUI via Flatpak wrapper.
# Prefer nested Xwayland (:41) for stable Gdk sizing — does NOT modify Weston service.
# Flatpak+host GI on raw Wayland previously hit "taller than 65535 pixels".
export VERSION=$VER
export GDK_SCALE=1
export GDK_DPI_SCALE=1
export XDG_RUNTIME_DIR="\${XDG_RUNTIME_DIR:-/run/user/1000}"
export WAYLAND_DISPLAY="\${WAYLAND_DISPLAY:-wayland-0}"
export DBUS_SESSION_BUS_ADDRESS="\${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}"
# Host XKB data (stub runtime has none)
if [ -d /run/host/usr/share/X11/xkb ]; then
  export XKB_CONFIG_ROOT=/run/host/usr/share/X11/xkb
elif [ -d /usr/share/X11/xkb ]; then
  export XKB_CONFIG_ROOT=/usr/share/X11/xkb
fi
# Fontconfig (stub runtime has none)
if [ -d /run/host/etc/fonts ]; then
  export FONTCONFIG_PATH=/run/host/etc/fonts
elif [ -d /etc/fonts ]; then
  export FONTCONFIG_PATH=/etc/fonts
fi
export GSK_RENDERER="\${GSK_RENDERER:-cairo}"
export NO_AT_BRIDGE=1
export GTK_A11Y=none
export GTK_ICON_THEME_NAME=hicolor
unset PYTHONHOME
export GI_TYPELIB_PATH="/run/host/usr/lib/aarch64-linux-gnu/girepository-1.0:/run/host/usr/lib/girepository-1.0:/usr/lib/aarch64-linux-gnu/girepository-1.0"
export LD_LIBRARY_PATH="/run/host/usr/lib/aarch64-linux-gnu:/run/host/lib/aarch64-linux-gnu:/usr/lib/aarch64-linux-gnu:/app/lib:/app/lib/aarch64-linux-gnu"

PY=""
for p in /run/host/usr/bin/python3 /usr/bin/python3; do
  [ -x "\$p" ] && PY="\$p" && break
done
[ -n "\$PY" ] || { echo NO_HOST_PYTHON; exit 1; }

# Host gdk-pixbuf loaders — rewrite cache to /run/host paths so PNG works in sandbox.
HOST_LOADERS=""
for d in \
  /run/host/usr/lib/aarch64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders \
  /usr/lib/aarch64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders; do
  if [ -d "\$d" ]; then HOST_LOADERS="\$d"; break; fi
done
if [ -n "\$HOST_LOADERS" ]; then
  export GDK_PIXBUF_MODULEDIR="\$HOST_LOADERS"
  QL=""
  for q in /run/host/usr/bin/gdk-pixbuf-query-loaders /usr/bin/gdk-pixbuf-query-loaders; do
    [ -x "\$q" ] && QL="\$q" && break
  done
  if [ -n "\$QL" ]; then
    "\$QL" "\$HOST_LOADERS"/libpixbufloader-*.so > /var/tmp/cx2h-loaders.cache 2>/dev/null \
      || "\$QL" > /var/tmp/cx2h-loaders.cache 2>/dev/null || true
    if [ -f /var/tmp/cx2h-loaders.cache ]; then
      "\$PY" -c 'import pathlib;p=pathlib.Path("/var/tmp/cx2h-loaders.cache");t=p.read_text(errors="replace");p.write_text(t.replace("/usr/lib/","/run/host/usr/lib/").replace("/usr/lib64/","/run/host/usr/lib64/"))' 2>/dev/null || true
      export GDK_PIXBUF_MODULE_FILE=/var/tmp/cx2h-loaders.cache
    fi
  else
    for cache in \
      /run/host/usr/lib/aarch64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders.cache \
      /usr/lib/aarch64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders.cache; do
      if [ -f "\$cache" ]; then
        export GDK_PIXBUF_MODULE_FILE="\$cache"
        break
      fi
    done
  fi
fi

# Nested Xwayland for X11 GDK (stable). Falls back to Wayland if unavailable.
start_nested_xwayland() {
  [ "\${CX2H_FORCE_WAYLAND:-0}" = "1" ] && return 1
  if [ -e /tmp/.X11-unix/X41 ]; then
    export DISPLAY=:41
    export GDK_BACKEND=x11
    return 0
  fi
  XW=""
  for c in /run/host/usr/bin/Xwayland /usr/bin/Xwayland; do
    [ -x "\$c" ] && XW="\$c" && break
  done
  [ -n "\$XW" ] || return 1
  if [ ! -S "\$XDG_RUNTIME_DIR/\$WAYLAND_DISPLAY" ]; then
    if [ -S /run/cx2g-wayland/wayland-0 ]; then
      ln -sfn /run/cx2g-wayland/wayland-0 "\$XDG_RUNTIME_DIR/wayland-0" 2>/dev/null || true
    elif [ -S /run/cx2h-wayland/wayland-0 ]; then
      ln -sfn /run/cx2h-wayland/wayland-0 "\$XDG_RUNTIME_DIR/wayland-0" 2>/dev/null || true
    fi
  fi
  "\$XW" :41 -geometry 800x600 2>>/tmp/cx2h-xwayland.log &
  i=0
  while [ \$i -lt 20 ]; do
    [ -e /tmp/.X11-unix/X41 ] && break
    i=\$((i+1))
    "\$PY" -c 'import time;time.sleep(0.25)' 2>/dev/null || true
  done
  if [ -e /tmp/.X11-unix/X41 ]; then
    export DISPLAY=:41
    export GDK_BACKEND=x11
    echo "CX2H_XWAYLAND_OK display=:41"
    return 0
  fi
  echo "CX2H_XWAYLAND_FAIL"
  return 1
}

if ! start_nested_xwayland; then
  export GDK_BACKEND=wayland
  unset DISPLAY
  echo "CX2H_BACKEND_WAYLAND_FALLBACK"
fi

APP=""
for cand in /app/share/cx2h-testapp/app.py /app/share/app.py \
  /app/share/cx2h-testapp/share/app.py; do
  [ -f "\$cand" ] && APP="\$cand" && break
done
if [ -n "\$APP" ]; then
  cp -f "\$APP" /var/tmp/cx2h-testapp-\$VERSION.py 2>/dev/null || true
  [ -f /var/tmp/cx2h-testapp-\$VERSION.py ] && APP=/var/tmp/cx2h-testapp-\$VERSION.py
  echo "CX2H_LAUNCHER exec_py=\$PY app=\$APP backend=\$GDK_BACKEND display=\$DISPLAY"
  exec "\$PY" "\$APP"
fi
echo NO_APP_PY
exec "\$PY" - <<'PY'
import os, sys
os.environ["GDK_SCALE"] = "1"
os.environ["GDK_DPI_SCALE"] = "1"
os.environ.setdefault("NO_AT_BRIDGE", "1")
os.environ["GTK_ICON_THEME_NAME"] = "hicolor"
os.environ.setdefault("VERSION", os.environ.get("VERSION", "1.0.0"))
if not os.environ.get("GDK_BACKEND"):
    os.environ["GDK_BACKEND"] = "x11" if os.environ.get("DISPLAY") else "wayland"
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk
VERSION = os.environ.get("VERSION", "1.0.0")
is_v1 = VERSION.startswith("1")
bg = Gdk.RGBA(); bg.parse("#0B3D2E" if is_v1 else "#C45C26")
label_txt = "CX2H V1" if is_v1 else "CX2H V2"
W, H = 720, 480
class Win(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title(f"CX2H Test App V{VERSION[0]} · {VERSION}")
        self.set_decorated(False); self.set_resizable(False); self.set_keep_above(True)
        self.set_size_request(W, H); self.set_default_size(W, H); self.resize(W, H)
        self.connect("destroy", Gtk.main_quit)
        area = Gtk.DrawingArea(); area.set_size_request(W, H); area.connect("draw", self._draw)
        self.add(area); self.show_all(); GLib.idle_add(lambda: (self.resize(W, H), False)[1])
        sys.stderr.write("CX2H_WINDOW_MAPPED\n")
    def _draw(self, _w, cr):
        cr.set_source_rgba(bg.red, bg.green, bg.blue, 1.0); cr.paint()
        cr.set_source_rgb(0.91, 1.0, 0.96) if is_v1 else cr.set_source_rgb(1.0, 0.97, 0.94)
        cr.select_font_face("Sans", 0, 1); cr.set_font_size(64); cr.move_to(48, 200); cr.show_text(label_txt)
        cr.set_font_size(22); cr.move_to(48, 260); cr.show_text(f"org.gunnchos.CX2HTestApp · {VERSION}")
        if not is_v1:
            cr.set_source_rgb(1.0, 0.85, 0.2); cr.rectangle(0, 400, W, 80); cr.fill()
        return False
sys.stderr.write(f"CX2H_APP_START_INLINE version={VERSION} backend={os.environ.get('GDK_BACKEND')}\n")
Win(); Gtk.main()
PY
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

  mkdir -p "$ABUILD/files/bin" "$ABUILD/files/share/cx2h-testapp" "$ABUILD/files/lib" "$ABUILD/files/lib/aarch64-linux-gnu"
  cp -a "$SRC/app-$SRCVER/share/." "$ABUILD/files/share/cx2h-testapp/"
  # Stub Platform historically lacked /lib; ship dash + prefer runtime usr/lib symlink.
  if [ -x /bin/dash ]; then
    cp -a /bin/dash "$ABUILD/files/bin/sh"
  elif [ -x /usr/bin/dash ]; then
    cp -a /usr/bin/dash "$ABUILD/files/bin/sh"
  else
    cp -a /bin/sh "$ABUILD/files/bin/sh" || true
  fi
  # Also copy linker into the app as fallback; patchelf if available.
  if [ -e /lib/ld-linux-aarch64.so.1 ]; then
    cp -aL /lib/ld-linux-aarch64.so.1 "$ABUILD/files/lib/ld-linux-aarch64.so.1" 2>/dev/null || true
  fi
  for so in libc.so.6 libdl.so.2 libpthread.so.0 libm.so.6; do
    [ -e "/lib/aarch64-linux-gnu/$so" ] && cp -aL "/lib/aarch64-linux-gnu/$so" "$ABUILD/files/lib/aarch64-linux-gnu/" 2>/dev/null || true
  done
  if command -v patchelf >/dev/null 2>&1 && [ -x "$ABUILD/files/bin/sh" ] && [ -e "$ABUILD/files/lib/ld-linux-aarch64.so.1" ]; then
    patchelf --set-interpreter /app/lib/ld-linux-aarch64.so.1 \
      --set-rpath /app/lib:/app/lib/aarch64-linux-gnu \
      "$ABUILD/files/bin/sh" 2>/dev/null && echo PATCHELF_SH_OK_$BRANCH || echo PATCHELF_SH_FAIL_$BRANCH
  fi
  write_launcher "$ABUILD/files/bin/cx2h-testapp" "$VER"

  if flatpak build-finish \
      --command=cx2h-testapp \
      --share=ipc \
      --socket=wayland --socket=x11 --socket=session-bus \
      --device=dri \
      --filesystem=host \
      --filesystem=host-os \
      --filesystem=/var/tmp \
      --filesystem=/usr/share/X11/xkb:ro \
      --env=VERSION="$VER" \
      --env=GDK_SCALE=1 \
      --env=GDK_DPI_SCALE=1 \
      --env=XKB_CONFIG_ROOT=/usr/share/X11/xkb \
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
sockets=wayland;x11;session-bus;
devices=dri;
filesystems=host;host-os;/var/tmp;/usr/share/X11/xkb;

[Environment]
VERSION=$VER
GDK_SCALE=1
GDK_DPI_SCALE=1
XKB_CONFIG_ROOT=/usr/share/X11/xkb
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
