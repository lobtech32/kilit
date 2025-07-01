import socket
from datetime import datetime
import time

HOST = '0.0.0.0'
PORT = 40341

IMEI = "862205059210023"
USER_ID = 1234

def make_cmd(command: str):
    now = datetime.utcnow().strftime('%y%m%d%H%M%S')
    return f"*CMDS,OM,{IMEI},{now},{command}#\n".encode("utf-8")

def build_l0():
    timestamp = int(time.time())
    return make_cmd(f"L0,0,{USER_ID},{timestamp}")

def build_s5():
    return make_cmd("S5")

def build_g0():
    return make_cmd("G0")

def build_d0():
    return make_cmd("D0")

def handle_client(conn, addr):
    print(f"[+] Bağlantı kuruldu: {addr}")
    buffer = b""
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data
            try:
                msg = buffer.decode("utf-8")
                print(f"[📩] Gelen veri:\n{msg.strip()}")
                if "*CMDR" in msg and IMEI in msg:
                    print("🟢 Kilit bağlandı. Komutlar sırayla gönderiliyor...\n")

                    time.sleep(1)
                    conn.sendall(b'\xFF\xFF' + build_l0())
                    print("➡️ L0 gönderildi (kilit aç)\n")
                    time.sleep(1)

                    conn.sendall(b'\xFF\xFF' + build_s5())
                    print("➡️ S5 gönderildi (durum bilgisi)\n")
                    time.sleep(1)

                    conn.sendall(b'\xFF\xFF' + build_g0())
                    print("➡️ G0 gönderildi (firmware bilgisi)\n")
                    time.sleep(1)

                    conn.sendall(b'\xFF\xFF' + build_d0())
                    print("➡️ D0 gönderildi (konum isteği)\n")

                buffer = b""
            except UnicodeDecodeError:
                continue
        except ConnectionResetError:
            break
    print(f"[-] Bağlantı kapandı: {addr}")
    conn.close()

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