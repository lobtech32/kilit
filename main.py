import datetime

# 🔹 CRC hesaplayan fonksiyon
def calculate_crc(message_body: str) -> str:
    crc = 0
    for char in message_body:
        crc ^= ord(char)
    return f"{crc:02X}"

# 🔹 Komutu oluşturan fonksiyon
def build_oc30_command(imei: str, timestamp: str, command_body: str) -> str:
    base = f"CMDS,OM,{imei},{timestamp},{command_body}"
    crc = calculate_crc(base)
    return f"*{base}#{crc}"

# 🔹 GPS modülünü açan fonksiyon
def send_gps_enable_command(socket, imei):
    now = datetime.datetime.utcnow()
    timestamp = now.strftime("%y%m%d%H%M%S")  # YYMMDDHHMMSS
    komut = build_oc30_command(imei, timestamp, "D0,1")
    print(f"[➡️] GPS modülü açılıyor: {komut}")
    socket.sendall(komut.encode())