#!/usr/bin/env python3
"""AT-SPI driver: Export as PDF from LibreOffice Writer (GUI path)."""

from __future__ import annotations

import json
import sys
import time


def main() -> int:
    dest = sys.argv[1] if len(sys.argv) > 1 else "/var/lib/cx2h2/vault/files/cx2h2_j1_essay.pdf"
    try:
        import gi

        gi.require_version("Atspi", "2.0")
        from gi.repository import Atspi
    except Exception as ex:
        print(json.dumps({"ok": False, "error": f"atspi_import:{ex}"}))
        return 0

    Atspi.init()
    desktop = Atspi.get_desktop(0)
    menus = []
    buttons = []
    entries = []

    def walk(node, depth=0):
        if node is None or depth > 12:
            return
        try:
            name = node.get_name() or ""
            role = (node.get_role_name() or "").lower()
            if role in ("menu", "menu item", "menu bar"):
                menus.append({"name": name, "role": role, "depth": depth})
            if role in ("push button", "button"):
                buttons.append({"name": name, "role": role, "depth": depth})
            if role in ("text", "entry", "password text"):
                entries.append({"name": name, "role": role, "depth": depth})
            for i in range(min(node.get_child_count() or 0, 60)):
                walk(node.get_child_at_index(i), depth + 1)
        except Exception:
            return

    def click_named(needles):
        found = []

        def walk_click(node, depth=0):
            if node is None or depth > 12:
                return False
            try:
                name = (node.get_name() or "").lower()
                role = (node.get_role_name() or "").lower()
                if any(n in name for n in needles) and role in (
                    "menu item",
                    "push button",
                    "button",
                    "link",
                ):
                    found.append({"name": node.get_name(), "role": role})
                    for i in range(node.get_n_actions() or 0):
                        an = (node.get_action_name(i) or "").lower()
                        if an in ("click", "press", "activate"):
                            node.do_action(i)
                            return True
                    if (node.get_n_actions() or 0) > 0:
                        node.do_action(0)
                        return True
                for i in range(min(node.get_child_count() or 0, 60)):
                    if walk_click(node.get_child_at_index(i), depth + 1):
                        return True
            except Exception:
                return False
            return False

        ok = walk_click(desktop)
        return ok, found

    walk(desktop)
    # Step through File → Export As → Export as PDF
    steps = []
    for needles in (
        ["file"],
        ["export as", "export"],
        ["export as pdf", "export directly as pdf", "pdf"],
    ):
        ok, found = click_named(needles)
        steps.append({"needles": needles, "ok": ok, "found": found[:10]})
        time.sleep(0.8)
        desktop = Atspi.get_desktop(0)

    # Fill filename entry if dialog present
    filled = False

    def fill(node, depth=0):
        nonlocal filled
        if node is None or depth > 12 or filled:
            return
        try:
            role = (node.get_role_name() or "").lower()
            if role in ("text", "entry", "password text"):
                try:
                    if hasattr(node, "set_text_contents"):
                        node.set_text_contents(dest)
                        filled = True
                        return
                except Exception:
                    pass
            for i in range(min(node.get_child_count() or 0, 60)):
                fill(node.get_child_at_index(i), depth + 1)
        except Exception:
            return

    fill(Atspi.get_desktop(0))
    # Click Save/Export/OK
    ok_save, found_save = click_named(["save", "export", "ok", "open"])
    steps.append({"needles": ["save/export/ok"], "ok": ok_save, "found": found_save[:10], "filled": filled})

    print(
        json.dumps(
            {
                "ok": any(s.get("ok") for s in steps),
                "filled": filled,
                "steps": steps,
                "menus_sample": menus[:40],
                "buttons_sample": buttons[:20],
                "dest": dest,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
