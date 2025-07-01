import socket
from datetime import datetime, timezone
import time

HOST = '0.0.0.0'
PORT = 40341

IMEI = "862205059210023"

def get_time_str():
    return datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')

def build_position_request():
    ts = get_time_str()
    cmd = f"*CMDS,OM,{IMEI},{ts},D0#\n"
    return b'\xFF\xFF' + cmd.encode()

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    # Tek konum isteği
    req = build_position_request()
    conn.sendall(req)
    print(f"[➡️] Konum isteği gönderildi:\n{req.decode().strip()}")

    buf = b""
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buf += data
            try:
                msg = buf.decode().strip()
                print(f"[📩] Gelen veri: {msg}")
                buf = b""
            except UnicodeDecodeError:
                # eksik veri parçalanırsa bekle
                continue
    except ConnectionResetError:
        pass
    finally:
        conn.close()
        print(f"[-] Bağlantı kapandı: {addr}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"[🚀] Sunucu çalışıyor: {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            handle_client(conn, addr)

if __name__ == "__main__":
    start_server()