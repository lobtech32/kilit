import socket
import threading
import time
from datetime import datetime

HOST = "0.0.0.0"
PORT = 40341
IMEI = "862205059210023"

def build_d0_command():
    now = datetime.utcnow().strftime("%y%m%d%H%M%S")
    return f"*CMDS,OM,{IMEI},{now},D0#".encode()

def send_d0(conn):
    d0_cmd = build_d0_command()
    conn.sendall(d0_cmd)
    print(f"[➡️] D0 komutu gönderildi:\n{d0_cmd.decode()}")

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    buffer = b""
    last_send_time = 0

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            buffer += data
            try:
                msg = buffer.decode(errors="ignore").strip()
                for line in msg.split("#"):
                    if not line.strip():
                        continue
                    full_msg = line.strip() + "#"
                    print(f"[📩] Gelen veri: {full_msg}")

                    if "*CMDR" in full_msg and IMEI in full_msg:
                        if ",L1," in full_msg:
                            print("📍 Konum verisi alındı, 10 dakika sonra tekrar istenecek.")
                            last_send_time = time.time()

                now = time.time()
                if now - last_send_time >= 600:  # 10 dakika
                    send_d0(conn)
                    last_send_time = now

                buffer = b""

            except UnicodeDecodeError:
                continue

    except ConnectionResetError:
        print(f"[-] Bağlantı kesildi: {addr}")
    finally:
        conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"[🚀] Sunucu çalışıyor: {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    start_server()