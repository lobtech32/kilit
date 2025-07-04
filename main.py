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

def gps_command():
    now = datetime.datetime.utcnow().strftime('%d%m%y%H%M%S')
    raw = f"*CMDS,OM,{IMEI},{now},D1,1"
    return f"{raw}#{crc16(raw)}".encode()

def parse_location(msg):
    if ",L1," in msg:
        parts = msg.split(",")
        if len(parts) >= 7:
            lat = parts[5]
            lon = parts[6]
            if lat == "0" and lon == "0":
                return "LBS boş", False
            return f"LBS konumu: {lat}, {lon}", True
        return "Geçersiz L1 verisi", False
    elif ",L0," in msg:
        return "📍 ✅ GPS verisi geldi!", True
    return None, False

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    try:
        while True:
            # Komut gönder
            cmd = gps_command()
            conn.sendall(cmd)
            print(f"[➡️] D1 komutu gönderildi:\n{cmd.decode()}")

            timeout = time.time() + 15
            success = False

            while time.time() < timeout:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    msg = data.decode(errors='ignore').strip()
                    print(f"[📩] Gelen veri: {msg}")

                    if "*CMDR,OM" in msg:
                        yorum, success = parse_location(msg)
                        if yorum:
                            print("📍", yorum)
                        if success:
                            break
                except Exception as e:
                    print(f"[!] Veri okuma hatası: {e}")
                    break

            if not success:
                print("🚫 Konum verisi alınamadı veya geçersiz.")
            
            print("🕓 10 dakika bekleniyor...\n")
            time.sleep(600)
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