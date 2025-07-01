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
    readable = f"*CMDS,OM,{IMEI},{ts},D0#\n"
    raw = b'\xFF\xFF' + readable.encode('utf-8')
    return raw, readable

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    
    # konum komutu hazırla ve gönder
    raw_cmd, readable_cmd = build_position_request()
    try:
        conn.sendall(raw_cmd)
        print(f"[➡️] Konum isteği gönderildi:\n{readable_cmd.strip()}")
    except Exception as e:
        print(f"[HATA] Komut gönderilemedi: {e}")
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
                decoded = buffer.decode('utf-8', errors='ignore').strip()
                print(f"[📩] Gelen veri: {decoded}")
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