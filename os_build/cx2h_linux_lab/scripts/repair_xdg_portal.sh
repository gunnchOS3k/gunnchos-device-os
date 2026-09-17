#!/bin/bash
# CX2H: coherent gunnchos portal session on systemd user bus + Weston Wayland socket
set -eu
mkdir -p /tmp/cx2h-portal

if [ "$(id -u)" -eq 0 ]; then
  if ! command -v gdbus >/dev/null 2>&1; then
    apt-get update -qq >/tmp/cx2h-portal/apt.out 2>&1 || true
    apt-get install -y -qq libglib2.0-bin >/tmp/cx2h-portal/apt.out 2>&1 || true
  fi
  # Widen GTK UseIn
  mkdir -p /usr/share/xdg-desktop-portal/portals /etc/xdg/xdg-desktop-portal
  cat >/usr/share/xdg-desktop-portal/portals/gtk.portal <<'P'
[portal]
DBusName=org.freedesktop.impl.portal.desktop.gtk
Interfaces=org.freedesktop.impl.portal.FileChooser;org.freedesktop.impl.portal.AppChooser;org.freedesktop.impl.portal.Print;org.freedesktop.impl.portal.Notification;org.freedesktop.impl.portal.Inhibit;org.freedesktop.impl.portal.Access;org.freedesktop.impl.portal.Account;org.freedesktop.impl.portal.Email;org.freedesktop.impl.portal.DynamicLauncher;org.freedesktop.impl.portal.Lockdown;org.freedesktop.impl.portal.Settings;
UseIn=gnome;GunnchOS;GNOME;weston;wlroots;Unity;LXDE
P
  cat >/etc/xdg/xdg-desktop-portal/gunnchos-portals.conf <<'C'
[preferred]
default=gtk;
C
  chmod 777 /run/cx2g-wayland/wayland-0 2>/dev/null || true
  chmod 1777 /run/cx2g-wayland 2>/dev/null || true
  # Expose Weston socket into the real user runtime
  mkdir -p /run/user/1000
  chown gunnchos:gunnchos /run/user/1000
  ln -sfn /run/cx2g-wayland/wayland-0 /run/user/1000/wayland-0
  # Also keep a gunnchos bus at the Chromium unit path for coherence
  fuser -k /run/cx2g-wayland/bus 2>/dev/null || true
  rm -f /run/cx2g-wayland/bus
  # Prefer linking the working user bus into the CX graphical path Chromium already uses
  if [ -S /run/user/1000/bus ]; then
    ln -sfn /run/user/1000/bus /run/cx2g-wayland/bus
    echo LINKED_USER_BUS_TO_CX_PATH
  else
    runuser -u gunnchos -- dbus-daemon --session --address=unix:path=/run/cx2g-wayland/bus --fork
    chmod 777 /run/cx2g-wayland/bus
    chown gunnchos:gunnchos /run/cx2g-wayland/bus
  fi
  ls -la /run/user/1000/bus /run/user/1000/wayland-0 /run/cx2g-wayland/bus /run/cx2g-wayland/wayland-0 2>/dev/null || true
  # Patch Chromium shell unit to use user bus + GNOME desktop hint
  if [ -f /etc/systemd/system/cx2g-gunnch-shell.service ]; then
    sed -i 's|DBUS_SESSION_BUS_ADDRESS=.*|DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus|' /etc/systemd/system/cx2g-gunnch-shell.service || true
    grep -q XDG_CURRENT_DESKTOP= /etc/systemd/system/cx2g-gunnch-shell.service \
      || sed -i '/\[Service\]/a Environment=XDG_CURRENT_DESKTOP=GNOME' /etc/systemd/system/cx2g-gunnch-shell.service
    grep -q 'XDG_RUNTIME_DIR=/run/user/1000' /etc/systemd/system/cx2g-gunnch-shell.service \
      || sed -i 's|Environment=XDG_RUNTIME_DIR=.*|Environment=XDG_RUNTIME_DIR=/run/user/1000|' /etc/systemd/system/cx2g-gunnch-shell.service || true
    systemctl daemon-reload || true
  fi
  exec runuser -u gunnchos -- env \
    XDG_RUNTIME_DIR=/run/user/1000 \
    DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
    WAYLAND_DISPLAY=wayland-0 \
    XDG_CURRENT_DESKTOP=GNOME \
    XDG_SESSION_TYPE=wayland \
    GDK_BACKEND=wayland \
    "$0" --as-user
fi

export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export XDG_CURRENT_DESKTOP=GNOME
export XDG_SESSION_TYPE=wayland
export GDK_BACKEND=wayland
unset DISPLAY || true

pkill -u gunnchos -f '/usr/libexec/xdg-desktop-portal' 2>/dev/null || true
pkill -u gunnchos -f 'xdg-desktop-portal-gtk' 2>/dev/null || true
sleep 1

echo STEP_portal_start user=$(whoami) bus=$DBUS_SESSION_BUS_ADDRESS xdg=$XDG_RUNTIME_DIR wayland=$WAYLAND_DISPLAY
ls -la "$XDG_RUNTIME_DIR/wayland-0" "$XDG_RUNTIME_DIR/bus" 2>/dev/null || true
dbus-send --session --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus \
  org.freedesktop.DBus.ListNames >/tmp/cx2h-portal/dbus_names.txt 2>/tmp/cx2h-portal/dbus_err.txt || true
echo DBUS_LIST_RC=$?
head -5 /tmp/cx2h-portal/dbus_names.txt || true

XDP=/usr/libexec/xdg-desktop-portal
XDP_GTK=/usr/libexec/xdg-desktop-portal-gtk
echo XDP=$XDP XDP_GTK=$XDP_GTK

# Import env into systemd --user so activation works
systemctl --user import-environment XDG_RUNTIME_DIR WAYLAND_DISPLAY XDG_SESSION_TYPE XDG_CURRENT_DESKTOP DBUS_SESSION_BUS_ADDRESS 2>/dev/null || true
systemctl --user set-environment WAYLAND_DISPLAY=wayland-0 XDG_SESSION_TYPE=wayland XDG_CURRENT_DESKTOP=GNOME 2>/dev/null || true

nohup "$XDP_GTK" >/tmp/cx2h-portal/xdp-gtk.log 2>&1 & echo GTK_PID=$!
sleep 2
if ! kill -0 "${GTK_PID:-0}" 2>/dev/null; then
  echo GTK_DIED_first; cat /tmp/cx2h-portal/xdp-gtk.log || true
  # Retry without forcing GDK_BACKEND
  unset GDK_BACKEND || true
  nohup "$XDP_GTK" >/tmp/cx2h-portal/xdp-gtk.log 2>&1 & echo GTK_PID=$!
  sleep 2
fi
nohup "$XDP" --replace >/tmp/cx2h-portal/xdp.log 2>&1 & echo PORTAL_PID=$!
sleep 5

# If systemd user units exist, also try them
systemctl --user restart xdg-desktop-portal.service 2>/dev/null || true
systemctl --user restart xdg-desktop-portal-gtk.service 2>/dev/null || true
sleep 2

ps -eo user,pid,args | grep -E 'xdg-desktop-portal' | grep -v grep || true
echo ---XDP_LOG---
tail -120 /tmp/cx2h-portal/xdp.log || true
echo ---GTK_LOG---
tail -120 /tmp/cx2h-portal/xdp-gtk.log || true

dbus-send --session --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus \
  org.freedesktop.DBus.ListNames 2>/dev/null | grep -i portal || echo NO_PORTAL_NAMES

INTRO_OUT=/tmp/cx2h-portal/introspect.xml
gdbus introspect --session --dest org.freedesktop.portal.Desktop \
  --object-path /org/freedesktop/portal/desktop >"$INTRO_OUT" 2>/tmp/cx2h-portal/intro.err || true
head -160 "$INTRO_OUT" || true
grep -E 'portal\.(FileChooser|OpenURI|Settings|Notification)' "$INTRO_OUT" && echo IFACE_CORE_OK || echo IFACE_CORE_MISSING
echo PORTAL_START_DONE bus=$DBUS_SESSION_BUS_ADDRESS
