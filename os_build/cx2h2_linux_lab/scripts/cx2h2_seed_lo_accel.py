#!/usr/bin/env python3
"""Seed a LibreOffice user profile with Export Directly as PDF → Ctrl+Shift+E."""

from __future__ import annotations

import sys
from pathlib import Path

XCU = """<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry"
 xmlns:xs="http://www.w3.org/2001/XMLSchema"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
 <item oor:path="/org.openoffice.Office.Accelerators/PrimaryKeys/Modules/com.sun.star.text.TextDocument">
  <node oor:name="Ctrl+Shift+E" oor:op="replace">
   <prop oor:name="Command" oor:type="xs:string">
    <value>.uno:ExportToPDF</value>
   </prop>
  </node>
 </item>
 <item oor:path="/org.openoffice.Office.Accelerators/PrimaryKeys/Global">
  <node oor:name="Ctrl+Shift+E" oor:op="replace">
   <prop oor:name="Command" oor:type="xs:string">
    <value>.uno:ExportToPDF</value>
   </prop>
  </node>
 </item>
</oor:items>
"""


def main() -> int:
    profile = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cx2h2-lo-profile")
    user = profile / "user"
    user.mkdir(parents=True, exist_ok=True)
    (user / "registrymodifications.xcu").write_text(XCU)
    print(str(user / "registrymodifications.xcu"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
