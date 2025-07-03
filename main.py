import socket
import datetime
import threading
import time
import zlib
import logging

# Log ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

HOST = '0.0.0.0'
PORT = 40341
IMEI = '862205059210023'
GPS_TIMEOUT = 180  # 3 dakika (GPS fix süresi)

def crc16(data):
    crc = zlib.crc32(data.encode()) & 0xFFFF
    return f"{crc:04X}"

def build_command(command_type):
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%d%m%y%H%M%S')
    raw = f"*CMDS,OM,{IMEI},{now},{command_type}"
    return f"{raw}#{crc16(raw)}".encode()

def handle_client(conn, addr):
    logging.info(f"[+] Yeni bağlantı: {addr}")
    try:
        # İlk GPS isteği
        conn.sendall(build_command("D0"))
        logging.info("[➡️] D0 komutu gönderildi (ilk istek)")

        while True:
            data = conn.recv(1024)
            if not data:
                break

            msg = data.decode(errors='ignore').strip()
            logging.info(f"[📩] Gelen veri: {msg}")

            if "*CMDR" in msg and IMEI in msg:
                if ",D0," in msg:
                    if "A,," not in msg:  # Geçerli GPS verisi kontrolü
                        logging.warning("GPS verisi geçersiz veya yok!")
                        time.sleep(GPS_TIMEOUT)  # Yeni deneme öncesi bekle
                    else:
                        logging.info("✅ Geçerli GPS verisi alındı!")
                        time.sleep(600)  # 10 dakika bekle

                elif ",L1," in msg:
                    logging.info("🔒 Kilit kapatıldı, GPS isteği gönderiliyor...")
                    time.sleep(2)  # Kısa bekleme
                    conn.sendall(build_command("D0"))

    except Exception as e:
        logging.error(f"[!] Hata: {e}")
    finally:
        conn.close()
        logging.info(f"[-] Bağlantı kapandı: {addr}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        logging.info(f"[🚀] Sunucu çalışıyor: {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()