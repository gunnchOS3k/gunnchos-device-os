#!/usr/bin/env python3
"""CX2H Test App v2 — undecorated DrawingArea, visually distinct from v1."""
from __future__ import annotations

import os
import sys

os.environ["GDK_SCALE"] = "1"
os.environ["GDK_DPI_SCALE"] = "1"
os.environ.setdefault("VERSION", "2.0.0")
os.environ.setdefault("NO_AT_BRIDGE", "1")
os.environ.setdefault("GTK_A11Y", "none")
os.environ["GTK_ICON_THEME_NAME"] = "hicolor"
if not os.environ.get("GDK_BACKEND"):
    os.environ["GDK_BACKEND"] = "x11" if os.environ.get("DISPLAY") else "wayland"

try:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GLib, Gtk
except Exception as exc:  # pragma: no cover
    sys.stderr.write(f"GTK_IMPORT_FAIL:{exc}\n")
    raise SystemExit(2)

VERSION = os.environ.get("VERSION", "2.0.0")
BG = Gdk.RGBA()
BG.parse("#C45C26")
WIN_W, WIN_H = 720, 480


class Cx2hWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title(f"CX2H Test App V2 · {VERSION}")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_accept_focus(True)
        self.set_size_request(WIN_W, WIN_H)
        self.set_default_size(WIN_W, WIN_H)
        self.resize(WIN_W, WIN_H)
        try:
            self.set_icon_list([])
        except Exception:
            pass
        self.connect("destroy", Gtk.main_quit)
        self.connect("delete-event", lambda *_: Gtk.main_quit() or False)

        area = Gtk.DrawingArea()
        area.set_size_request(WIN_W, WIN_H)
        area.connect("draw", self._on_draw)
        self.add(area)
        self.show_all()
        GLib.idle_add(self._assert_size)
        sys.stderr.write("CX2H_WINDOW_MAPPED\n")
        sys.stderr.flush()

    def _assert_size(self) -> bool:
        self.resize(WIN_W, WIN_H)
        self.set_size_request(WIN_W, WIN_H)
        return False

    def _on_draw(self, _widget, cr) -> bool:
        cr.set_source_rgba(BG.red, BG.green, BG.blue, 1.0)
        cr.paint()
        cr.set_source_rgb(1.0, 0.97, 0.94)
        cr.select_font_face("Sans", 0, 1)
        cr.set_font_size(64)
        cr.move_to(48, 200)
        cr.show_text("CX2H V2")
        cr.set_font_size(22)
        cr.move_to(48, 260)
        cr.show_text(f"org.gunnchos.CX2HTestApp · {VERSION}")
        cr.set_source_rgb(1.0, 0.85, 0.2)
        cr.rectangle(0, 400, WIN_W, 80)
        cr.fill()
        return False


def main() -> int:
    try:
        settings = Gtk.Settings.get_default()
        if settings is not None:
            settings.set_property("gtk-decoration-layout", "")
            settings.set_property("gtk-icon-theme-name", "hicolor")
            settings.set_property("gtk-button-images", False)
            settings.set_property("gtk-menu-images", False)
    except Exception:
        pass
    sys.stderr.write(
        f"CX2H_APP_START version={VERSION} gdk_backend={os.environ.get('GDK_BACKEND')} "
        f"display={os.environ.get('DISPLAY')} wayland={os.environ.get('WAYLAND_DISPLAY')}\n"
    )
    sys.stderr.flush()
    Cx2hWindow()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
