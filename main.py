import socket
from datetime import datetime, timezone
import time

HOST = '0.0.0.0'
PORT = 40341

IMEI = "862205059210023"
USER_ID = 1234  # Örnek kullanıcı numarası

def get_time_str():
    # UTC timezone-aware time string, yyMMddHHmmss formatında
    return datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')

def build_unlock_command():
    time_str = get_time_str()
    timestamp = int(time.time())
    cmd = f"*CMDS,OM,{IMEI},{time_str},L0,0,{USER_ID},{timestamp}#\n"
    return b'\xFF\xFF' + cmd.encode('utf-8')

def build_location_request_command():
    time_str = get_time_str()
    timestamp = int(time.time())
    # Konum talep komutu protokolü örnek, cihaz protokolüne göre değiştirilebilir
    cmd = f"*CMDG,OM,{IMEI},{time_str},L1,0,{USER_ID},{timestamp}#\n"
    return b'\xFF\xFF' + cmd.encode('utf-8')

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    buffer = b""
    unlock_sent = False
    last_processed_message = None

    last_location_request = 0
    location_response_received = False

    try:
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                buffer += data

                try:
                    message = buffer.decode("utf-8").strip()
                    # Gelen veri çoğu zaman tek mesajdır, bazen birleşik olabilir

                    # Aynı mesajı tekrar işleme
                    if message == last_processed_message:
                        buffer = b""
                        continue

                    last_processed_message = message

                    print(f"[📩] Gelen veri: {message}")

                    # Kilit açma komutu gönderme koşulu
                    if "*CMDR" in message and IMEI in message:
                        parts = message.split(',')
                        # parts[3] mesajdaki tarih alanı: "000000000000" olmamalı
                        if len(parts) > 3 and parts[3] != "000000000000":
                            if not unlock_sent:
                                print("🔓 Kilit bağlandı. Açma komutu gönderiliyor...")
                                unlock_cmd = build_unlock_command()
                                conn.sendall(unlock_cmd)
                                print(f"[➡️] Açma komutu gönderildi:\n{unlock_cmd.decode(errors='ignore')}")
                                unlock_sent = True
                                last_location_request = time.time()  # konum talebi için zaman sıfırlanır
                        else:
                            print("⏳ Geçersiz zaman damgası, açma komutu gönderilmedi.")

                    # Konum yanıtı örneği "*GPSR" içeriyorsa kabul edelim (protokole göre değiştirilebilir)
                    if "*GPSR" in message and IMEI in message:
                        print("📍 Konum yanıtı alındı.")
                        location_response_received = True
                        last_location_request = time.time()

                    buffer = b""
                except UnicodeDecodeError:
                    # Eksik veya bozuk veri olabilir, bekle
                    continue

                # Kilit açıldıysa konum talebi döngüsü
                if unlock_sent:
                    now = time.time()
                    # Yanıt geldiyse 30 sn sonra, gelmediyse 5 dk sonra tekrar konum iste
                    if (location_response_received and now - last_location_request > 30) or (not location_response_received and now - last_location_request > 300):
                        print("📡 Konum talebi gönderiliyor...")
                        loc_cmd = build_location_request_command()
                        conn.sendall(loc_cmd)
                        last_location_request = now
                        location_response_received = False

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