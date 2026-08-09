#!/usr/bin/env python3
"""Ring input sample — destructive gestures require confirmation."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gunnchos_adopter_sdk import AdopterClient


def main() -> None:
    client = AdopterClient()
    print(client.sample_ring_input("tap"))
    print(client.sample_ring_input("swipe_delete_hint"))


if __name__ == "__main__":
    main()
