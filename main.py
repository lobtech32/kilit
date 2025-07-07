import socket
import datetime
import threading
import time
import zlib

HOST = '0.0.0.0'
PORT = 40341
IMEI = '862205059216418'

def crc16(data):
    crc = zlib.crc32(data.encode()) & 0xFF
    return f"{crc:02X}"

def send_command(cmd_code, param=None):
    now = datetime.datetime.utcnow().strftime('%d%m%y%H%M%S')
    raw = f"*CMDS,OM,{IMEI},{now},{cmd_code}"
    if param:
        raw += f",{param}"
    packet = f"{raw}#{crc16(raw)}"
    return packet.encode()

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    try:
        # Başlangıçta D1,60 gönder
        d1 = send_command("D1", "60")
        conn.sendall(d1)
        print(f"[➡️] D1 komutu gönderildi: {d1.decode()}")

        # Ardından S5 gönder
        time.sleep(1)
        s5 = send_command("S5")
        conn.sendall(s5)
        print(f"[➡️] S5 komutu gönderildi: {s5.decode()}")

        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode(errors='ignore').strip()
            print(f"[📩] Gelen veri: {msg}")

            if ",L1," in msg or ",L0," in msg:
                print("📍 Konum verisi geldi.")
            elif ",S5," in msg:
                print("🔐 Kilit durumu verisi geldi (S5).")
            elif ",Q0," in msg:
                print("🔄 Q0: Cihaz yeniden bağlandı, komutları yeniden göndermek gerekebilir.")
                # Tekrar D1 ve S5 gönder
                conn.sendall(d1)
                conn.sendall(s5)

            time.sleep(1)

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