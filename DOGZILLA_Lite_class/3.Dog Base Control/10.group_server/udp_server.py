from socket import *
import time

# 广播地址和端口（'<broadcast>' 表示发送到所有子网）
broadcast_address = ('<broadcast>', 6001)  # 或者用 '255.255.255.255'

# 创建UDP套接字，并启用广播
s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)  # 启用广播

try:
    while True:
        a = input("please input data:")
        if a == 1 or a == '1' : #开始表演
            s.sendto(b'1', broadcast_address)  # 发送 '1'
            print("Broadcast sent: 1")

        else: #停止表演
            s.sendto(b'0', broadcast_address)  # 发送 '0'
            print("Broadcast sent: 0")

except KeyboardInterrupt:
    print("Server stopped")
finally:
    s.close()