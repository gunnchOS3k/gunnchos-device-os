"""python -m gunnchos_device_os.cloud_dev_plane"""

from gunnchos_device_os.cloud_dev_plane.server import serve_forever_from_env

if __name__ == "__main__":
    serve_forever_from_env()
