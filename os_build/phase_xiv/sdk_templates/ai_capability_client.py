#!/usr/bin/env python3
"""Call OS AI System API — never model paths."""
import json, urllib.request

def invoke(capability: str, text: str, base: str = "http://127.0.0.1:8788"):
    req = urllib.request.Request(
        f"{base}/v1/capability/{capability}",
        data=json.dumps({"user_id": "dev", "input": text}).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
