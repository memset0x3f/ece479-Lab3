import bluetooth

server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_sock.bind(("", bluetooth.PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]
uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"  # 自定义UUID

bluetooth.advertise_service(server_sock, "RPiBT", service_id=uuid,
                          service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
                          profiles=[bluetooth.SERIAL_PORT_PROFILE])

print("等待连接...")
client_sock, client_info = server_sock.accept()
print("已连接:", client_info)
import time
try:
    while True:
        data = "test"
        time.sleep(0.01)
        client_sock.send(data)
        if data.lower() == "exit":
            break
finally:
    client_sock.close()
    server_sock.close()