import socket
from datetime import datetime, timezone

def calculate_crc(message_body: str) -> str:
    crc = 0
    for char in message_body:
        crc ^= ord(char)
    return f"{crc:02X}"

def build_oc30_command(imei: str, timestamp: str, command_body: str) -> str:
    base = f"CMDS,OM,{imei},{timestamp},{command_body}"
    crc = calculate_crc(base)
    return f"*{base}#{crc}"

def send_gps_enable_command(client_socket, imei):
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%y%m%d%H%M%S")
    command = build_oc30_command(imei, timestamp, "D0,1")
    print(f"[➡️] GPS modülü açılıyor: {command}")
    client_socket.sendall(command.encode())

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 40341))
    server.listen(5)
    print("Sunucu dinlemede...")

    while True:
        client_socket, addr = server.accept()
        print(f"Yeni bağlantı: {addr}")
        try:
            while True:
                data = client_socket.recv(1024).decode()
                if not data:
                    print("Bağlantı kapandı.")
                    break
                print(f"Gelen veri: {data}")

                if "*CMDR" in data:
                    parts = data.split(",")
                    if len(parts) >= 3:
                        imei = parts[2]
                        send_gps_enable_command(client_socket, imei)
                    else:
                        print("IMEI çözümlenemedi, gelen veri eksik.")
        except Exception as e:
            print(f"Hata: {e}")
        finally:
            client_socket.close()

if __name__ == "__main__":
    main()