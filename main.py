#!/usr/bin/env python3
import socket
import threading
import time
from datetime import datetime
import struct
import logging

# ------------------- KONFİGÜRASYON -------------------
HOST = "0.0.0.0"
PORT = 40341
IMEI = "862205059210023"
LOG_LEVEL = logging.INFO
# -----------------------------------------------------

# Log ayarları
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('oc30_server.log'),
        logging.StreamHandler()
    ]
)

def calculate_crc16(data):
    """CRC16 hesaplama (Modbus)"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc

def build_command(command_type):
    """OC30 komut oluşturucu"""
    now = datetime.utcnow().strftime("%y%m%d%H%M%S")
    cmd_str = f"*CMDS,OM,{IMEI},{now},{command_type}#"
    
    # 0xFFFF header ekleme
    cmd_bytes = cmd_str.encode()
    full_cmd = struct.pack('>H', 0xFFFF) + cmd_bytes
    
    logging.debug(f"Oluşturulan komut: {full_cmd}")
    return full_cmd

def parse_gps_data(data):
    """D0 yanıtını parse etme"""
    try:
        parts = data.split(',')
        if len(parts) < 13 or parts[6] != 'A':
            return None
        
        # Enlem/Boylam çevrimi
        lat = float(parts[7][:2]) + float(parts[7][2:])/60
        if parts[8] == 'S':
            lat = -lat
            
        lon = float(parts[9][:3]) + float(parts[9][3:])/60
        if parts[10] == 'W':
            lon = -lon
            
        return {
            'timestamp': parts[5],
            'latitude': lat,
            'longitude': lon,
            'satellites': int(parts[11]),
            'accuracy': float(parts[12])
        }
    except Exception as e:
        logging.error(f"GPS parse hatası: {e}")
        return None

class OC30Handler:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.last_command_time = 0
        self.command_interval = 600  # 10 dakika (saniye)
        
    def send_command(self, command_type):
        try:
            cmd = build_command(command_type)
            self.conn.sendall(cmd)
            logging.info(f"{command_type} komutu gönderildi")
            return True
        except Exception as e:
            logging.error(f"Komut gönderme hatası: {e}")
            return False
            
    def handle_data(self, data):
        try:
            # CRC kontrolü (isteğe bağlı)
            if len(data) > 2:
                received_crc = struct.unpack('>H', data[-2:])[0]
                calculated_crc = calculate_crc16(data[:-2])
                if received_crc != calculated_crc:
                    logging.warning("CRC uyuşmazlığı!")
            
            message = data.decode('latin-1').strip()
            for line in message.split('#'):
                if not line.strip():
                    continue
                    
                full_msg = line + '#'
                logging.info(f"Alınan veri: {full_msg}")
                
                if "*CMDR" in full_msg and IMEI in full_msg:
                    if ",D0," in full_msg:
                        gps_data = parse_gps_data(full_msg)
                        if gps_data:
                            logging.info(f"GPS Verisi: {gps_data}")
                            # Burada MQTT'ye veya veritabanına kaydedebilirsiniz
                            
                    elif ",L1," in full_msg:
                        logging.info("Kilit kapatıldı")
                        self.last_command_time = time.time()
                        
        except UnicodeDecodeError as e:
            logging.warning(f"Decode hatası: {e}")
            
    def run(self):
        try:
            buffer = b""
            while True:
                data = self.conn.recv(1024)
                if not data:
                    break
                    
                buffer += data
                self.handle_data(buffer)
                buffer = b""
                
                # Periyodik D0 komutu gönder
                if time.time() - self.last_command_time > self.command_interval:
                    if self.send_command("D0"):
                        self.last_command_time = time.time()
                        
        except ConnectionResetError:
            logging.warning(f"Bağlantı kesildi: {self.addr}")
        finally:
            self.conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        logging.info(f"Sunucu başlatıldı: {HOST}:{PORT}")
        
        while True:
            conn, addr = s.accept()
            logging.info(f"Yeni bağlantı: {addr}")
            handler = OC30Handler(conn, addr)
            thread = threading.Thread(target=handler.run)
            thread.start()

if __name__ == "__main__":
    start_server()