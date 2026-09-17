#!/usr/bin/env python3
"""QEMU usernet guestfwd `-cmd:` TCP relay (stdin/stdout ↔ host TCP).

QEMU `guestfwd=tcp:GADDR:GPORT-tcp:HADDR:HPORT` can accept guest SYNs while
failing to deliver non-trivial request payloads (OPTIONS/POST) to the host
listener — host proxy then never logs the request and the guest sees
empty_http_response. Spawning a fresh per-connection relay via `-cmd:` is an
additive Device Lab workaround that fully copies bytes in both directions.

Usage (invoked by QEMU; avoid commas in the cmd string — they break netdev
parsing):
  python3 hub_guestfwd_cmd_relay.py 127.0.0.1 8787
"""
from __future__ import annotations

import fcntl
import os
import select
import socket
import sys


def _set_nonblock(fd: int) -> None:
    try:
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    except OSError:
        pass


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        sys.stderr.write("usage: hub_guestfwd_cmd_relay.py HOST PORT\n")
        return 2
    host, port_s = args[0], args[1]
    port = int(port_s)
    upstream = socket.create_connection((host, port), timeout=10.0)
    upstream.setblocking(False)
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    _set_nonblock(stdin.fileno())
    _set_nonblock(stdout.fileno())
    try:
        peer_open = True
        up_open = True
        while peer_open or up_open:
            readers: list[object] = []
            if peer_open:
                readers.append(stdin)
            if up_open:
                readers.append(upstream)
            if not readers:
                break
            readable, _, _ = select.select(readers, [], [], 30.0)
            if not readable:
                break
            if stdin in readable and peer_open:
                try:
                    chunk = stdin.read(65536)
                except BlockingIOError:
                    chunk = b""
                if not chunk:
                    peer_open = False
                    try:
                        upstream.shutdown(socket.SHUT_WR)
                    except OSError:
                        pass
                else:
                    upstream.sendall(chunk)
            if upstream in readable and up_open:
                try:
                    chunk = upstream.recv(65536)
                except BlockingIOError:
                    chunk = b""
                if not chunk:
                    up_open = False
                else:
                    stdout.write(chunk)
                    stdout.flush()
    finally:
        try:
            upstream.close()
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
