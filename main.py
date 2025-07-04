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
    raw = f"*CMDS,OM,{IMEI},{now},D1,1"  # D0 yerine D1 komutu
    packet = f"{raw}#{crc16(raw)}"
    return packet.encode()

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    try:
        while True:
            req = gps_request()
            conn.sendall(req)
            print(f"[➡️] D1 komutu gönderildi:\n{req.decode(errors='ignore')}")

            timeout = time.time() + 20  # 20 saniye içinde cevap bekle
            received_location = False

            while time.time() < timeout:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    msg = data.decode(errors='ignore').strip()
                    print(f"[📩] Gelen veri: {msg}")

                    if ",L1," in msg:
                        print("📍 Konum verisi alındı, 10 dakika sonra tekrar istenecek.\n")
                        received_location = True
                        break
                    elif ",Q0," in msg:
                        print("⚠️ Cihaz ağa yeni bağlandı, komut tekrar gönderilecek.")
                        time.sleep(2)
                        conn.sendall(req)  # komutu tekrar gönder
                except Exception as e:
                    print(f"[!] Veri okuma hatası: {e}")
                    break

            if not received_location:
                print("⚠️ Konum verisi alınamadı, 10 dakika sonra tekrar denenecek.\n")

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