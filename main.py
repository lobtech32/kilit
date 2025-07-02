import socket
import time
import datetime
import threading

HOST = '0.0.0.0'
PORT = 40341
IMEI = '862205059210023'

def crc_xor(hex_str):
    xor_result = 0
    for i in range(0, len(hex_str), 2):
        xor_result ^= int(hex_str[i:i+2], 16)
    return '{:02X}'.format(xor_result)

def build_command(cmd_code):
    now = datetime.datetime.utcnow()
    timestamp = now.strftime('%d%m%y%H%M%S')
    raw = f'*CMDS,OM,{IMEI},{timestamp},{cmd_code}#'
    hex_data = raw.encode().hex().upper()
    crc = crc_xor(hex_data)
    return raw.encode() + crc.encode()

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    request = build_command("D0,1")  # Sadece konum isteği
    conn.sendall(request)
    print(f"[➡️] D0 komutu gönderildi:\n{request.decode(errors='ignore')}")

    last_location = time.time()

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            try:
                message = data.decode('utf-8')
            except UnicodeDecodeError:
                print("⚠️ Gelen veri çözülemedi (UTF-8 dışı karakter)")
                continue

            print(f"[📩] Gelen veri: {message.strip()}")
            if "*CMDR" in message and ",L1," in message:
                print("📍 Konum verisi alındı, 10 dakika sonra tekrar istenecek.")
                last_location = time.time()
            elif "*CMDR" in message and ",L0," in message:
                print("❌ Konum alınamadı. Tekrar deneniyor...")

            if time.time() - last_location >= 600:
                request = build_command("D0,1")
                conn.sendall(request)
                print(f"[📤] Yeniden konum istendi:\n{request.decode(errors='ignore')}")
                last_location = time.time()

            time.sleep(2)
    except Exception as e:
        print(f"[HATA] {e}")
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
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    start_server()