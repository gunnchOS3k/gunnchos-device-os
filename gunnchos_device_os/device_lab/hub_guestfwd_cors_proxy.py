"""Device Lab Hub guestfwd CORS/logging proxy (additive, non-reductive).

QEMU guestfwd delivers guest TCP to host loopback. WebKitGTK custom-protocol
pages (Origin: http://ipc.localhost) issue CORS preflight before
POST /api/v1/auth/login. The Hub app historically had no CORSMiddleware, so
preflight could hang or fail closed before any non-healthz access line appeared
on uvicorn — even when TCP ESTABLISHED and guest HTTP/1.0 healthz worked.

This proxy:
  - listens on the guestfwd target (127.0.0.1:8787)
  - answers OPTIONS locally with permissive Device Lab CORS
  - forwards other methods to the real Hub upstream (127.0.0.1:8788)
  - injects Access-Control-* on responses
  - appends access lines to a proxy log for bind proof / diagnosis

Does not reduce Hub surface area; production durable CORS still belongs in
WAIKE Hub (separate DRAFT PR).
"""
from __future__ import annotations

import argparse
import asyncio
import time
from pathlib import Path

DEFAULT_LISTEN = ("127.0.0.1", 8787)
DEFAULT_UPSTREAM = ("127.0.0.1", 8788)

# Tauri custom-protocol + common WebKitGTK origins seen in Device Lab.
_ALLOWED_ORIGINS = frozenset(
    {
        "http://ipc.localhost",
        "https://ipc.localhost",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
        "null",
    }
)


def _cors_headers(origin: str | None) -> list[tuple[bytes, bytes]]:
    allow = origin if origin and (origin in _ALLOWED_ORIGINS or origin == "null") else "*"
    # Reflect known origins; wildcard otherwise (Device Lab sidecar only).
    if allow != "*" and origin:
        allow = origin
    return [
        (b"Access-Control-Allow-Origin", allow.encode("latin1", "replace")),
        (b"Access-Control-Allow-Methods", b"GET, POST, PUT, PATCH, DELETE, OPTIONS"),
        (
            b"Access-Control-Allow-Headers",
            b"Content-Type, Authorization, X-Waike-Actor-Id, X-Waike-Actor-Role, "
            b"Access-Control-Request-Private-Network",
        ),
        (b"Access-Control-Allow-Private-Network", b"true"),
        (b"Access-Control-Max-Age", b"600"),
        (b"Vary", b"Origin"),
    ]


def _header_block(headers: list[tuple[bytes, bytes]]) -> bytes:
    return b"".join(k + b": " + v + b"\r\n" for k, v in headers) + b"\r\n"


async def _read_headers(reader: asyncio.StreamReader) -> tuple[bytes, list[tuple[bytes, bytes]], bytes]:
    buf = b""
    while b"\r\n\r\n" not in buf and len(buf) < 65536:
        chunk = await reader.read(4096)
        if not chunk:
            break
        buf += chunk
    head, _, rest = buf.partition(b"\r\n\r\n")
    lines = head.split(b"\r\n")
    request_line = lines[0] if lines else b""
    headers: list[tuple[bytes, bytes]] = []
    for ln in lines[1:]:
        if b":" not in ln:
            continue
        k, _, v = ln.partition(b":")
        headers.append((k.strip(), v.strip()))
    return request_line, headers, rest


def _header_value(headers: list[tuple[bytes, bytes]], name: bytes) -> str | None:
    lname = name.lower()
    for k, v in headers:
        if k.lower() == lname:
            return v.decode("latin1", "replace")
    return None


def _log_line(log_path: Path, line: str) -> None:
    try:
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(line.rstrip() + "\n")
            fh.flush()
    except OSError:
        pass


async def _handle(
    client_reader: asyncio.StreamReader,
    client_writer: asyncio.StreamWriter,
    *,
    upstream: tuple[str, int],
    log_path: Path,
) -> None:
    peer = client_writer.get_extra_info("peername")
    peer_s = f"{peer[0]}:{peer[1]}" if peer else "unknown"
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _log_line(log_path, f"{stamp} INFO:     {peer_s} - ACCEPT")
    try:
        request_line, headers, body_prefix = await asyncio.wait_for(
            _read_headers(client_reader), timeout=12.0
        )
        if not request_line:
            _log_line(
                log_path,
                f"{stamp} INFO:     {peer_s} - EMPTY_REQUEST "
                f"prefix_len={len(body_prefix)}",
            )
            return
        method = request_line.split(b" ", 1)[0].decode("latin1", "replace")
        bits = request_line.split(b" ")
        path_q = bits[1].decode("latin1", "replace") if len(bits) > 1 else "/"
        http_ver = bits[2].decode("latin1", "replace") if len(bits) > 2 else "?"
        origin = _header_value(headers, b"Origin")
        clen = int(_header_value(headers, b"Content-Length") or "0")
        remaining = max(0, clen - len(body_prefix))
        if remaining:
            body_prefix += await client_reader.readexactly(remaining)

        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _log_line(
            log_path,
            f'{stamp} INFO:     {peer_s} - "{method} {path_q} {http_ver}" PROXY '
            f"origin={origin!r} clen={clen}",
        )

        if method.upper() == "OPTIONS":
            resp_headers = _cors_headers(origin) + [
                (b"Content-Length", b"0"),
                (b"Connection", b"close"),
            ]
            # HTTP/1.0 clients tolerate 1.1 status; keep 1.0 if asked.
            status_line = (
                b"HTTP/1.0 204 No Content\r\n"
                if http_ver.startswith("HTTP/1.0")
                else b"HTTP/1.1 204 No Content\r\n"
            )
            client_writer.write(status_line + _header_block(resp_headers))
            await client_writer.drain()
            _log_line(
                log_path,
                f'{stamp} INFO:     {peer_s} - "OPTIONS {path_q} {http_ver}" 204 CORS_LOCAL',
            )
            return

        up_reader, up_writer = await asyncio.open_connection(upstream[0], upstream[1])
        try:
            # Rebuild request; force Connection: close for guestfwd stability.
            filtered = [
                (k, v)
                for k, v in headers
                if k.lower() not in {b"connection", b"proxy-connection", b"keep-alive"}
            ]
            filtered.append((b"Connection", b"close"))
            # Prefer HTTP/1.0 toward upstream when guest used 1.0 (guestfwd hygiene).
            up_req_line = request_line
            if http_ver.startswith("HTTP/1.0"):
                up_req_line = method.encode("latin1") + b" " + path_q.encode("latin1") + b" HTTP/1.0"
            up_writer.write(up_req_line + b"\r\n" + _header_block(filtered) + body_prefix)
            await up_writer.drain()

            up_status_line, up_headers, up_body = await _read_headers(up_reader)
            if not up_status_line:
                client_writer.write(b"HTTP/1.1 502 Bad Gateway\r\nConnection: close\r\n\r\n")
                await client_writer.drain()
                return
            status_bits = up_status_line.split(b" ", 2)
            status_code = status_bits[1].decode("latin1", "replace") if len(status_bits) > 1 else "?"
            # Drop upstream Connection / CORS; inject Device Lab CORS.
            out_headers = [
                (k, v)
                for k, v in up_headers
                if k.lower()
                not in {
                    b"connection",
                    b"keep-alive",
                    b"transfer-encoding",  # we buffer content-length body below when present
                    b"access-control-allow-origin",
                    b"access-control-allow-methods",
                    b"access-control-allow-headers",
                    b"access-control-allow-private-network",
                }
            ]
            # If chunked, stream remainder without re-parsing; else honor Content-Length.
            te = (_header_value(up_headers, b"Transfer-Encoding") or "").lower()
            up_clen = _header_value(up_headers, b"Content-Length")
            out_headers.extend(_cors_headers(origin))
            out_headers.append((b"Connection", b"close"))

            if "chunked" in te:
                # Stream chunked as-is (re-add transfer-encoding).
                out_headers = [(k, v) for k, v in out_headers if k.lower() != b"transfer-encoding"]
                out_headers.append((b"Transfer-Encoding", b"chunked"))
                client_writer.write(up_status_line + b"\r\n" + _header_block(out_headers) + up_body)
                await client_writer.drain()
                while True:
                    chunk = await up_reader.read(65536)
                    if not chunk:
                        break
                    client_writer.write(chunk)
                    await client_writer.drain()
            else:
                body = up_body
                if up_clen is not None:
                    need = max(0, int(up_clen) - len(body))
                    if need:
                        body += await up_reader.readexactly(need)
                else:
                    # Read until EOF.
                    while True:
                        chunk = await up_reader.read(65536)
                        if not chunk:
                            break
                        body += chunk
                    out_headers = [(k, v) for k, v in out_headers if k.lower() != b"content-length"]
                    out_headers.append((b"Content-Length", str(len(body)).encode("ascii")))
                client_writer.write(up_status_line + b"\r\n" + _header_block(out_headers) + body)
                await client_writer.drain()

            _log_line(
                log_path,
                f'{stamp} INFO:     {peer_s} - "{method} {path_q} {http_ver}" {status_code} OK',
            )
        finally:
            up_writer.close()
            try:
                await up_writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass
    except asyncio.TimeoutError:
        _log_line(log_path, f"PROXY_TIMEOUT peer={peer_s} waiting_headers")
    except Exception as exc:  # noqa: BLE001
        _log_line(log_path, f"PROXY_ERROR peer={peer_s} err={exc!r}")
    finally:
        try:
            client_writer.close()
            await client_writer.wait_closed()
        except Exception:  # noqa: BLE001
            pass


async def run_proxy(
    *,
    listen_host: str,
    listen_port: int,
    upstream_host: str,
    upstream_port: int,
    log_path: Path,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _log_line(
        log_path,
        f"INFO:     hub_guestfwd_cors_proxy listening on http://{listen_host}:{listen_port} "
        f"→ {upstream_host}:{upstream_port}",
    )

    async def _client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await _handle(
            reader,
            writer,
            upstream=(upstream_host, upstream_port),
            log_path=log_path,
        )

    server = await asyncio.start_server(_client, listen_host, listen_port)
    async with server:
        await server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Device Lab Hub guestfwd CORS proxy")
    p.add_argument("--listen-host", default=DEFAULT_LISTEN[0])
    p.add_argument("--listen-port", type=int, default=DEFAULT_LISTEN[1])
    p.add_argument("--upstream-host", default=DEFAULT_UPSTREAM[0])
    p.add_argument("--upstream-port", type=int, default=DEFAULT_UPSTREAM[1])
    p.add_argument("--log", type=Path, required=True)
    args = p.parse_args(argv)
    asyncio.run(
        run_proxy(
            listen_host=args.listen_host,
            listen_port=args.listen_port,
            upstream_host=args.upstream_host,
            upstream_port=args.upstream_port,
            log_path=args.log,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
