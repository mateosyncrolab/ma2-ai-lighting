"""Cliente minimo para el telnet de grandMA2 (puerto 30000 por defecto).

Usa sockets directos: telnetlib ya no existe en Python 3.13+. La consola o el
onPC tienen que tener el acceso remoto por telnet habilitado.
"""

from __future__ import annotations

import socket
import time
from collections.abc import Callable, Iterable

DEFAULT_PORT = 30000


class MA2Telnet:
    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = 5.0,
                 delay: float = 0.05) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.delay = delay
        self._sock: socket.socket | None = None

    def __enter__(self) -> "MA2Telnet":
        self.connect()
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def connect(self) -> str:
        self._sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        return self._read()

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None

    def login(self, user: str, password: str = "") -> str:
        return self.send(f'Login "{user}" "{password}"')

    def send(self, command: str) -> str:
        if self._sock is None:
            raise RuntimeError("no conectado")
        if "\n" in command or "\r" in command:
            raise ValueError("un comando por linea")
        self._sock.sendall(command.encode("utf-8") + b"\r\n")
        time.sleep(self.delay)
        return self._read()

    def send_all(self, commands: Iterable[str],
                 on_reply: Callable[[int, str, str], None] | None = None) -> int:
        n = 0
        for n, cmd in enumerate(commands, 1):
            reply = self.send(cmd)
            if on_reply:
                on_reply(n, cmd, reply)
        return n

    def _read(self, idle: float = 0.15) -> str:
        """Lee lo que haya disponible hasta que la consola deje de escribir."""
        assert self._sock is not None
        chunks: list[bytes] = []
        self._sock.settimeout(idle)
        try:
            while True:
                data = self._sock.recv(4096)
                if not data:
                    break
                chunks.append(data)
        except (socket.timeout, TimeoutError):
            pass
        finally:
            self._sock.settimeout(self.timeout)
        return b"".join(chunks).decode("utf-8", errors="replace")
