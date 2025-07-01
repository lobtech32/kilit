import socket
from datetime import datetime, timezone
import time

HOST = '0.0.0.0'
PORT = 40341
IMEI = "862205059210023"

def build_d0_command():
    ts = datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')
    cmd_str = f"*CMDS,OM,{IMEI},{ts},D0#\n"
    full_cmd = b'\xFF\xFF' + cmd_str.encode('utf-8')
    return full_cmd, cmd_str

def parse_location_response(message):
    if ",D0," not in message:
        return None
    parts = message.split(',')
    if len(parts) < 13:
        return None
    try:
        lat_raw = parts[7]
        lat_dir = parts[8]
        lon_raw = parts[9]
        lon_dir = parts[10]
        if not lat_raw or not lon_raw or lat_dir not in ('N', 'S') or lon_dir not in ('E', 'W'):
            return None

        lat_deg = int(float(lat_raw) / 100)
        lat_min = float(lat_raw) - lat_deg * 100
        lat = lat_deg + (lat_min / 60.0)
        if lat_dir == 'S':
            lat = -lat

        lon_deg = int(float(lon_raw) / 100)
        lon_min = float(lon_raw) - lon_deg * 100
        lon = lon_deg + (lon_min / 60.0)
        if lon_dir == 'W':
            lon = -lon

        return lat, lon
    except Exception:
        return None

def handle_client(conn, addr):
    print(f"[+] Yeni bağlantı: {addr}")
    try:
        raw_cmd, readable_cmd = build_d0_command()
        conn.sendall(raw_cmd)
        print(f"[➡️] D0 komutu gönderildi:\n{readable_cmd.strip()}")
    except Exception as e:
        print(f"[HATA] Komut gönderilemedi: {e}")
        conn.close()
        return

    buffer = b""
    timeout = time.time() + 180  # 3 dakikalık timeout
    try:
        while time.time() < timeout:
            conn.settimeout(5)
            try:
                data = conn.recv(1024)
                if not data:
                    break
                buffer += data
                try:
                    decoded = buffer.decode('utf-8', errors='ignore').strip()
                    print(f"[📩] Gelen veri: {decoded}")
                    loc = parse_location_response(decoded)
                    if loc:
                        print(f"📍 Konum alındı: Enlem={loc[0]:.6f}, Boylam={loc[1]:.6f}")
                        break
                    buffer = b""
                except Exception as e:
                    print(f"[❗] Decode hatası: {e}")
                    continue
            except socket.timeout:
                continue
    except ConnectionResetError:
        print("[-] Bağlantı sıfırlandı.")
    finally:
        conn.close()
        print(f"[-] Bağlantı kapandı: {addr}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"[🚀] Sunucu çalışıyor: {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            handle_client(conn, addr)

if __name__ == "__main__":
    start_server()