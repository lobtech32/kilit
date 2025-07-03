import socket
import datetime
import threading
import time
import zlib

HOST = '0.0.0.0'
PORT = 40341
IMEI = '862205059210023'

def crc16(data):
    crc = zlib.crc32(data.encode()) & 0xFF
    return f"{crc:02X}"

def gps_request():
    now = datetime.datetime.utcnow().strftime('%d%m%y%H%M%S')
    raw = f"*CMDS,OM,{IMEI},{now},D0,1"
    packet = f"{raw}#{crc16(raw)}"
    return packet.encode()

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    try:
        while True:
            conn.sendall(gps_request())
            print(f"[➡️] D0 komutu gönderildi:")

            timeout = time.time() + 15  # 15 saniye içinde cevap bekle

            while time.time() < timeout:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    msg = data.decode(errors='ignore').strip()
                    print(f"[📩] Gelen veri: {msg}")

                    if ",L1," in msg:
                        print("📍 Konum verisi geldi (içerik kontrol edilmeli).")
                        break
                except Exception as e:
                    print(f"[!] Veri okuma hatası: {e}")
                    break

            print("🕓 10 dakika bekleniyor...\n")
            time.sleep(600)  # 10 dakika bekle
    except Exception as e:
        print(f"[!] Hata: {e}")
    finally:
        conn.close()
        print(f"[-] Bağlantı kapandı: {addr}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[🚀] Sunucu çalışıyor: {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()