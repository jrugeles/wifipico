# main.py — AP + HTTP estático index.html + /on /off /state (POST JSON) y GET->redirect
import network, socket, gc, time
from machine import Pin

# =================== CONFIG AP ===================
SSID     = "PicoW-AP"
PASSWORD = "12345678"        # '' para red abierta (no recomendado)
CHANNEL  = 6
IP       = "192.168.4.1"
MASK     = "255.255.255.0"
GW       = "192.168.4.1"
DNS      = "8.8.8.8"

HTML_FILE = "index.html"

# =================== HARDWARE ====================
LED = Pin("LED", Pin.OUT)
LED.value(0)

# =================== HTTP UTILS ==================
def http_send(conn, status="200 OK", ctype="text/html; charset=utf-8", body=b"", extra_headers=None):
    try:
        hdr = "HTTP/1.1 {}\r\nContent-Type: {}\r\nConnection: close\r\n".format(status, ctype)
        if extra_headers:
            for k, v in extra_headers.items():
                hdr += "{}: {}\r\n".format(k, v)
        hdr += "\r\n"
        conn.sendall(hdr.encode())
        if body:
            if isinstance(body, str):
                body = body.encode()
            conn.sendall(body)
    except Exception:
        pass

def http_redirect(conn, location="/"):
    http_send(conn, "302 Found", "text/plain; charset=utf-8", "Redirecting...", {"Location": location})

def read_request(conn):
    """
    Lee hasta ~1 KB (suficiente para la línea de petición y algunos headers),
    devuelve (method, path, raw_headers).
    """
    try:
        data = conn.recv(1024)
    except Exception:
        return None, None, b""
    if not data:
        return None, None, b""
    try:
        head, _ = data.split(b"\r\n\r\n", 1) if b"\r\n\r\n" in data else (data, b"")
        first = head.split(b"\r\n", 1)[0].decode()
        parts = first.split()
        method = parts[0] if len(parts) > 0 else "GET"
        target = parts[1] if len(parts) > 1 else "/"
        return method, target, head
    except Exception:
        return None, None, b""

def split_path_query(target):
    if not target:
        return "/", {}
    if "?" in target:
        path, qs = target.split("?", 1)
    else:
        path, qs = target, ""
    params = {}
    if qs:
        for pair in qs.split("&"):
            if not pair:
                continue
            if "=" in pair:
                k, v = pair.split("=", 1)
            else:
                k, v = pair, ""
            params[k] = v
    return path, params

# =================== AP ==========================
def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(False)
    time.sleep(0.1)
    try:
        ap.config(ssid=SSID, password=PASSWORD, channel=CHANNEL)
    except TypeError:
        ap.config(essid=SSID, password=PASSWORD, channel=CHANNEL)
    ap.ifconfig((IP, MASK, GW, DNS))
    ap.active(True)
    while not ap.active():
        time.sleep(0.05)
    return ap

# =================== CARGA HTML ==================
def load_index():
    try:
        with open(HTML_FILE, "rb") as f:
            return f.read()
    except OSError:
        return b"""<!doctype html>
<html><head><meta charset="utf-8"><title>index.html no encontrado</title></head>
<body><h3>Sube <code>index.html</code> a la raiz del dispositivo.</h3></body></html>"""

# =================== SERVER ======================
def serve(index_bytes):
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(addr)
    srv.listen(3)
    print("HTTP en http://{}/".format(IP))

    while True:
        try:
            conn, remote = srv.accept()
            method, target, _ = read_request(conn)
            if not target:
                http_send(conn, "400 Bad Request", "text/plain; charset=utf-8", "Bad Request")
                conn.close(); gc.collect(); continue

            path, params = split_path_query(target)

            # ruido navegador
            if path == "/favicon.ico":
                http_send(conn, "204 No Content", "text/plain; charset=utf-8", "")
                conn.close(); gc.collect(); continue

            # --- ON / OFF ---
            if path == "/on":
                if method == "POST":
                    LED.value(1)
                    http_send(conn, "200 OK", "application/json; charset=utf-8", b'{"ok":true,"on":true}')
                else:  # GET -> volver a "/"
                    LED.value(1)
                    http_redirect(conn, "/")
                conn.close(); gc.collect(); continue

            if path == "/off":
                if method == "POST":
                    LED.value(0)
                    http_send(conn, "200 OK", "application/json; charset=utf-8", b'{"ok":true,"on":false}')
                else:
                    LED.value(0)
                    http_redirect(conn, "/")
                conn.close(); gc.collect(); continue

            # Estado JSON
            if path == "/state":
                body = b'{"on":%s}' % (b"true" if LED.value() else b"false")
                http_send(conn, "200 OK", "application/json; charset=utf-8", body,
                          {"Cache-Control":"no-cache"})
                conn.close(); gc.collect(); continue

            # Raiz u otra ruta -> index.html (no cache para evitar html viejo)
            http_send(conn, "200 OK", "text/html; charset=utf-8", index_bytes,
                      {"Cache-Control":"no-cache"})
            conn.close()

        except Exception as e:
            try:
                http_send(conn, "500 Internal Server Error", "text/plain; charset=utf-8", "Internal Error")
                conn.close()
            except Exception:
                pass
        finally:
            gc.collect()

# =================== MAIN =======================
if __name__ == "__main__":
    ap = start_ap()
    print("AP activo  SSID:", SSID, "| IP:", ap.ifconfig()[0], "| Canal:", CHANNEL)
    index_bytes = load_index()
    serve(index_bytes)
