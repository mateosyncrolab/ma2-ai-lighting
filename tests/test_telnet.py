"""Prueba el cliente telnet contra un servidor TCP local que imita a la consola."""

import socket
import threading

from ma2tools.telnet import MA2Telnet


def servidor_falso():
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    recibido: list[str] = []

    def atender():
        conn, _ = srv.accept()
        conn.sendall(b"Welcome to grandMA2 telnet\r\n")
        buf = b""
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                buf += data
                while b"\r\n" in buf:
                    linea, buf = buf.split(b"\r\n", 1)
                    recibido.append(linea.decode())
                    conn.sendall(b"OK " + linea + b"\r\n")
        srv.close()

    hilo = threading.Thread(target=atender, daemon=True)
    hilo.start()
    return srv.getsockname()[1], recibido, hilo


def test_envia_y_lee_respuestas():
    port, recibido, hilo = servidor_falso()
    respuestas = []
    with MA2Telnet("127.0.0.1", port, delay=0) as tn:
        tn.login("operador", "1234")
        n = tn.send_all(["Fixture 1 Thru 4", "At 50"],
                        lambda i, c, r: respuestas.append(r))
    hilo.join(timeout=2)
    assert n == 2
    assert recibido == ['Login "operador" "1234"', "Fixture 1 Thru 4", "At 50"]
    assert "OK At 50" in respuestas[-1]


def test_rechaza_varias_lineas():
    port, _, hilo = servidor_falso()
    with MA2Telnet("127.0.0.1", port, delay=0) as tn:
        try:
            tn.send("At 0\r\nNewShow")
            assert False, "deberia fallar"
        except ValueError:
            pass
    hilo.join(timeout=2)
