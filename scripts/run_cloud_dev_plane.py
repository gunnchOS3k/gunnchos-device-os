#!/usr/bin/env python3
"""Launch the cloud DEV plane gateway (stdlib HTTP)."""
from gunnchos_device_os.cloud_dev_plane.server import serve_forever_from_env

if __name__ == "__main__":
    serve_forever_from_env()
