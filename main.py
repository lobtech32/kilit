import socket
import datetime
import threading
import time
import zlib

HOST = '0.0.0.0'
PORT = 40341
IMEI = '862205059216418'  # Yeni kilidin IMEI numarası

def crc16(data):
    crc = zlib.crc32(data.encode()) & 0xFF
    return f"{crc:02X}"

def build_command(cmd_type="D1", interval="60"):
    now = datetime.datetime.utcnow().strftime('%d%m%y%H%M%S')
    raw = f"*CMDS,OM,{IMEI},{now},{cmd_type},{interval}"
    return f"{raw}#{crc16(raw)}".encode()

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    try:
        while True:
            # D1 komutu gönder (her 60 saniyede bir konum iste)
            cmd = build_command("D1", "60")
            conn.sendall(cmd)
            print(f"[➡️] D1 komutu gönderildi:\n{cmd.decode()}")

            timeout = time.time() + 20  # 20 saniye içinde cevap bekle
            while time.time() < timeout:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    msg = data.decode(errors='ignore').strip()
                    print(f"[📩] Gelen veri: {msg}")

                    if ",L1," in msg:
                        if ",0,0,0" in msg:
                            print("📍 🚫 Sadece LBS konumu geldi. GPS henüz hazır değil.")
                        else:
                            print("📍 ✅ GPS konumu başarıyla alındı!")
                        break
                except Exception as e:
                    print(f"[!] Veri okuma hatası: {e}")
                    break

            print("🕓 60 saniye bekleniyor...\n")
            time.sleep(60)  # 1 dakika beklemeden sonra tekrar gönder
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