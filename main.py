import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 40341))
server.listen(5)
print("Sunucu dinlemede...")

while True:
    client_socket, addr = server.accept()
    print(f"Yeni bağlantı: {addr}")
    data = client_socket.recv(1024).decode()
    print(f"Gelen veri: {data}")
    # Burada istediğin işlemleri yap
    # Örnek: client_socket.sendall(b"Merhaba")