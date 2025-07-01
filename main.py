import socket
from datetime import datetime, timezone
import time

HOST = '0.0.0.0'
PORT = 40341

IMEI = "862205059210023"
USER_ID = 1234

def get_time_str():
    return datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')

def build_location_request_command():
    time_str = get_time_str()
    timestamp = int(time.time())
    cmd = f"*CMDG,OM,{IMEI},{time_str},L1,0,{USER_ID},{timestamp}#\n"
    return b'\xFF\xFF' + cmd.encode('utf-8')

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")

    try:
        # 📡 Sadece 1 defa konum talebi gönder
        loc_cmd = build_location_request_command()
        conn.sendall(loc_cmd)
        print(f"[➡️] Konum komutu gönderildi:\n{loc_cmd.decode(errors='ignore')}")

        buffer = b""
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data
            try:
                message = buffer.decode("utf-8").strip()
                print(f"[📩] Gelen veri: {message}")
                buffer = b""
            except UnicodeDecodeError:
                continue

    except ConnectionResetError:
        print(f"[-] Bağlantı kesildi: {addr}")
    finally:
        conn.close()
        print(f"[-] Bağlantı kapandı: {addr}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[🚀] Sunucu başlatıldı: {HOST}:{PORT}")
        while True:
            conn, addr = server_socket.accept()
            handle_client(conn, addr)

if __name__ == "__main__":
    start_server()