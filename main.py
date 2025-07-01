import socket
from datetime import datetime
import time

HOST = '0.0.0.0'
PORT = 40341

IMEI = "862205059210023"
USER_ID = 1234  # örnek kullanıcı numarası

def build_unlock_command():
    time_str = datetime.utcnow().strftime('%y%m%d%H%M%S')  # yyMMddHHmmss
    timestamp = int(time.time())  # Epoch
    cmd = f"*CMDS,OM,{IMEI},{time_str},L0,0,{USER_ID},{timestamp}#\n"
    return b'\xFF\xFF' + cmd.encode('utf-8')

def build_location_request_command():
    # Örnek konum talep komutu formatı, cihaz protokolüne göre değişebilir
    time_str = datetime.utcnow().strftime('%y%m%d%H%M%S')
    timestamp = int(time.time())
    cmd = f"*CMDG,OM,{IMEI},{time_str},L1,0,{USER_ID},{timestamp}#\n"
    return b'\xFF\xFF' + cmd.encode('utf-8')

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    buffer = b""
    unlock_sent = False
    last_location_request = 0
    location_response_received = False

    while True:
        try:
            # Veri alma
            data = conn.recv(1024)
            if not data:
                break
            buffer += data

            try:
                message = buffer.decode("utf-8")
                print(f"[📩] Gelen veri: {message.strip()}")

                # Kilit açma talebi alındıysa ve açma komutu gönderilmedi ise
                if "*CMDR" in message and IMEI in message and not unlock_sent:
                    print("🔓 Kilit bağlandı. Açma komutu gönderiliyor...")
                    unlock_cmd = build_unlock_command()
                    conn.sendall(unlock_cmd)
                    print(f"[➡️] Açma komutu gönderildi:\n{unlock_cmd.decode(errors='ignore')}")
                    unlock_sent = True
                    last_location_request = time.time()  # Konum talebi zaman sayacı başlat

                # Konum yanıtı alındıysa (örnek olarak "*GPSR" ile başlayan mesaj)
                if "*GPSR" in message and IMEI in message:
                    print("📍 Konum yanıtı alındı.")
                    location_response_received = True
                    last_location_request = time.time()

                buffer = b""

            except UnicodeDecodeError:
                continue

            # Kilit açıldıktan sonra konum talebi döngüsü
            if unlock_sent:
                now = time.time()
                # Eğer konum yanıtı alındı ve üzerinden 30 saniye geçtiyse ya da 5 dakikadan fazla yanıt gelmediyse tekrar konum isteği gönder
                if (location_response_received and now - last_location_request > 30) or (not location_response_received and now - last_location_request > 300):
                    print("📡 Konum talebi gönderiliyor...")
                    loc_cmd = build_location_request_command()
                    conn.sendall(loc_cmd)
                    last_location_request = now
                    location_response_received = False  # Yeni yanıt bekleniyor

            # Kısa bir uyku, CPU yükünü azaltmak için
            time.sleep(0.1)

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