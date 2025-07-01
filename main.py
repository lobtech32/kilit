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
    cmd_str = f"*CMDS,OM,{IMEI},{ts},D0#\n"
    full_cmd = b'\xFF\xFF' + cmd_str.encode('utf-8')
    return full_cmd, cmd_str  # hem ham veri hem okunabilir hali

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    
    # D0 komutunu hazırla
    req_bytes, req_str = build_position_request()
    
    try:
        conn.sendall(req_bytes)
        print(f"[➡️] Konum isteği gönderildi:\n{req_str.strip()}")
    except Exception as e:
        print(f"[HATA] Konum isteği gönderilemedi: {e}")
        conn.close()
        return

    buffer = b""
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data
            try:
                message = buffer.decode("utf-8", errors="ignore").strip()
                print(f"[📩] Gelen veri: {message}")
                buffer = b""
            except Exception as e:
                print(f"[❗] Decode hatası: {e}")
                continue
    except ConnectionResetError:
        print("[-] Bağlantı sıfırlandı.")
    finally:
        conn.close()
        print(f"[-] Bağlantı kapandı: {addr}")

def start_server():
    with socket.socket(socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"[🚀] Sunucu çalışıyor: {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            handle_client(conn, addr)

if __name__ == "__main__":
    start_server()