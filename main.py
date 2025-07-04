import socket
import datetime
import threading
import time
import zlib

HOST = '0.0.0.0'
PORT = 40341
IMEI = '862205059210023'

def crc8(data):  # D0 komutları için genelde 1 byte CRC yeterlidir
    crc = zlib.crc32(data.encode()) & 0xFF
    return f"{crc:02X}"

def create_d0_packet():
    now = datetime.datetime.utcnow().strftime('%d%m%y%H%M%S')
    raw = f"*CMDS,OM,{IMEI},{now},D0"
    packet = f"{raw}#{crc8(raw)}"
    return packet.encode()

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    try:
        while True:
            # 1. D0 komutunu gönder
            packet = create_d0_packet()
            conn.sendall(packet)
            print(f"[➡️] D0 komutu gönderildi:\n{packet.decode()}")

            # 2. Cevap bekle
            timeout = time.time() + 30  # 30 saniyelik pencere
            while time.time() < timeout:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    msg = data.decode(errors='ignore').strip()
                    print(f"[📩] Gelen veri: {msg}")

                    if msg.startswith("*CMDR") and ",D0," in msg:
                        print("📍 ✅ GPS konum verisi geldi.")
                        break
                    elif ",L1," in msg:
                        print("📍 🚫 Sadece LBS konumu geldi. GPS henüz hazır değil.")
                        break
                except Exception as e:
                    print(f"[!] Veri okuma hatası: {e}")
                    break

            # 3. 10 dakika bekle
            print("🕓 10 dakika bekleniyor...\n")
            time.sleep(600)

    except Exception as e:
        print(f"[!] Bağlantı hatası: {e}")
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