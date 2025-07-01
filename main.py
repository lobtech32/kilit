import socket
from datetime import datetime, timezone
import time

HOST = '0.0.0.0'
PORT = 40341

IMEI = "862205059210023"
USER_ID = 1234

def get_time_str():
    return datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')

def build_unlock_command():
    time_str = get_time_str()
    timestamp = int(time.time())
    cmd = f"*CMDS,OM,{IMEI},{time_str},L0,0,{USER_ID},{timestamp}#\n"
    return b'\xFF\xFF' + cmd.encode('utf-8')

def build_location_request_command():
    time_str = get_time_str()
    timestamp = int(time.time())
    cmd = f"*CMDG,OM,{IMEI},{time_str},L1,0,{USER_ID},{timestamp}#\n"
    return b'\xFF\xFF' + cmd.encode('utf-8')

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    buffer = b""
    unlock_sent = False
    location_loop_started = False
    last_location_request_time = 0
    location_response_received = False

    last_received_msg = None
    last_sent_msg_time = 0  # en son tekrar gönderme zamanı

    try:
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                buffer += data

                try:
                    message = buffer.decode("utf-8").strip()
                    print(f"[📩] Gelen veri: {message}")
                    buffer = b""

                    last_received_msg = message  # mesajı sakla

                    if not unlock_sent:
                        print("🔓 Kilit açma komutu gönderiliyor...")
                        unlock_cmd = build_unlock_command()
                        conn.sendall(unlock_cmd)
                        print(f"[➡️] Açma komutu:\n{unlock_cmd.decode(errors='ignore')}")
                        unlock_sent = True

                        print("📡 Konum talep komutu gönderiliyor...")
                        loc_cmd = build_location_request_command()
                        conn.sendall(loc_cmd)
                        print(f"[➡️] İlk konum komutu:\n{loc_cmd.decode(errors='ignore')}")
                        last_location_request_time = time.time()
                        location_loop_started = True

                    if "*GPSR" in message and IMEI in message:
                        print("📍 Konum yanıtı alındı.")
                        location_response_received = True
                        last_location_request_time = time.time()

                except UnicodeDecodeError:
                    continue

                now = time.time()

                # Gelen mesajı 5 dakikada bir tekrar gönder
                if last_received_msg and (now - last_sent_msg_time >= 300):  # 300 sn = 5 dk
                    print("🔁 5 dk geçti, son alınan mesaj tekrar gönderiliyor...")
                    try:
                        conn.sendall(last_received_msg.encode('utf-8'))
                        print(f"[➡️] Tekrar gönderilen mesaj:\n{last_received_msg}")
                        last_sent_msg_time = now
                    except Exception as e:
                        print(f"Mesaj tekrar gönderilemedi: {e}")

                # Konum döngüsü
                if location_loop_started:
                    if location_response_received and (now - last_location_request_time >= 30):
                        print("📡 [30sn sonra] Yeni konum talebi gönderiliyor...")
                        loc_cmd = build_location_request_command()
                        conn.sendall(loc_cmd)
                        print(f"[➡️] Konum komutu:\n{loc_cmd.decode(errors='ignore')}")
                        last_location_request_time = now
                        location_response_received = False

                    elif not location_response_received and (now - last_location_request_time >= 3600):  # 60 dk = 3600 sn
                        print("📡 [60dk sonra] Yeni konum talebi gönderiliyor (yanıt alınamadı)...")
                        loc_cmd = build_location_request_command()
                        conn.sendall(loc_cmd)
                        print(f"[➡️] Konum komutu:\n{loc_cmd.decode(errors='ignore')}")
                        last_location_request_time = now

                time.sleep(0.1)

            except ConnectionResetError:
                print(f"[-] Bağlantı kesildi: {addr}")
                break

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