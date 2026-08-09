#!/usr/bin/env python3
"""Connectivity sample."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gunnchos_adopter_sdk import AdopterClient


def main() -> None:
    client = AdopterClient()
    print(client.sample_connectivity())


if __name__ == "__main__":
    main()
