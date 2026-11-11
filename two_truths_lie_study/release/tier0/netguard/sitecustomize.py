"""Loaded by every Tier 0 subprocess (PYTHONPATH): refuse any socket connection that leaves the machine, so a step
that tried to reach the network would fail loudly instead of passing quietly. Loopback (used by multiprocessing on
some platforms) and Unix sockets stay allowed."""
import os
import socket

if os.environ.get("TIER0_NO_NETWORK") == "1":
    _connect = socket.socket.connect

    def _guarded(self, address):
        host = address[0] if isinstance(address, tuple) else None
        if host is not None and host not in ("127.0.0.1", "::1", "localhost"):
            raise OSError(f"Tier 0 is offline: refused connection to {address!r}")
        return _connect(self, address)

    socket.socket.connect = _guarded
    socket.create_connection = lambda address, *a, **k: (_ for _ in ()).throw(
        OSError(f"Tier 0 is offline: refused connection to {address!r}"))
