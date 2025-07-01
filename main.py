import socket
from datetime import datetime
import time

HOST = '0.0.0.0'
PORT = 40341

# Sabit bilgiler
IMEI = "862205059210023"
USER_ID = 1234  # örnek kullanıcı numarası

def build_unlock_command():
    time_str = datetime.utcnow().strftime('%y%m%d%H%M%S')  # yyMMddHHmmss
    timestamp = int(time.time())  # Epoch
    cmd = f"*CMDS,OM,{IMEI},{time_str},L0,0,{USER_ID},{timestamp}#\n"
    return b'\xFF\xFF' + cmd.encode('utf-8')

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    buffer = b""
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data
            try:
                message = buffer.decode("utf-8")
                print(f"[📩] Gelen veri: {message.strip()}")
                if "*CMDR" in message and IMEI in message:
                    print("🔓 Kilit bağlandı. Açma komutu gönderiliyor...")
                    unlock_cmd = build_unlock_command()
                    conn.sendall(unlock_cmd)
                    print(f"[➡️] Açma komutu gönderildi:\n{unlock_cmd.decode(errors='ignore')}")
                buffer = b""
            except UnicodeDecodeError:
                continue
        except ConnectionResetError:
            break
    print(f"[-] Bağlantı kapandı: {addr}")
    conn.close()

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