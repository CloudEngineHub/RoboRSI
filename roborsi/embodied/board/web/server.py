"""Board web server: the evolution dashboard (:8787)."""
from __future__ import annotations

import argparse
import asyncio
import socket

DEFAULT_EVO_PORT = 8787


def _port_free(host: str, port: int) -> bool:
    """True if (host, port) can be bound right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def serve(*, host: str = "127.0.0.1", evo_port: int = DEFAULT_EVO_PORT) -> int:
    """Run the evolution dashboard (blocking)."""
    if not _port_free(host, evo_port):
        print(f"[board.web] :{evo_port} already bound", flush=True)
        return 1
    import uvicorn

    from .evo_app import create_app
    asyncio.run(uvicorn.Server(uvicorn.Config(
        create_app(), host=host, port=evo_port, log_level="info")).serve())
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="RoboRSI evolution dashboard")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--evo-port", type=int, default=DEFAULT_EVO_PORT)
    a = ap.parse_args()
    serve(host=a.host, evo_port=a.evo_port)


if __name__ == "__main__":
    main()
