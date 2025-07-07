import socket
import datetime

def calculate_crc(message_body: str) -> str:
    crc = 0
    for char in message_body:
        crc ^= ord(char)
    return f"{crc:02X}"

def build_oc30_command(imei: str, timestamp: str, command_body: str) -> str:
    base = f"CMDS,OM,{imei},{timestamp},{command_body}"
    crc = calculate_crc(base)
    return f"*{base}#{crc}"

def send_gps_enable_command(socket, imei):
    now = datetime.datetime.utcnow()
    timestamp = now.strftime("%y%m%d%H%M%S")
    command = build_oc30_command(imei, timestamp, "D0,1")
    print(f"[➡️] GPS modülü açılıyor: {command}")
    socket.sendall(command.encode())

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 40341))
server.listen(5)
print("Sunucu dinlemede...")

while True:
    client_socket, addr = server.accept()
    print(f"Yeni bağlantı: {addr}")
    data = client_socket.recv(1024).decode()
    print(f"Gelen veri: {data}")

    if "*CMDR" in data:
        imei = data.split(",")[2]
        send_gps_enable_command(client_socket, imei)