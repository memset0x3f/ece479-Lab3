import asyncio
from bleak import BleakServer, BleakGATTCharacteristic

# 自定义服务UUID和特征UUID（可修改）
SERVICE_UUID = "0000FF01-0000-1000-8000-00805F9B34FB"
CHAR_TX_UUID = "0000FF02-0000-1000-8000-00805F9B34FB"  # PC -> 树莓派
CHAR_RX_UUID = "0000FF03-0000-1000-8000-00805F9B34FB"  # 树莓派 -> PC

async def main():
    # 创建BLE服务端
    server = BleakServer()
    
    # 定义服务
    service = server.add_service(SERVICE_UUID)
    
    # 添加特征：RX（可写，用于接收PC数据）
    char_rx = service.add_characteristic(
        CHAR_RX_UUID,
        properties=["write"],
    )
    
    # 添加特征：TX（可读+通知，用于发送数据到PC）
    char_tx = service.add_characteristic(
        CHAR_TX_UUID,
        properties=["read", "notify"],
    )
    
    # 启动服务并广播
    await server.start()
    print("BLE服务已启动，等待连接...")
    
    def on_disconnect(client):
        print(f"客户端断开: {client}")
    
    server.set_disconnected_callback(on_disconnect)
    
    # 处理数据接收（当PC写入CHAR_RX时触发）
    @char_rx.write_callback
    def on_rx_write(characteristic: BleakGATTCharacteristic, data: bytearray):
        print(f"收到PC数据: {data.decode('utf-8')}")
        # 示例：回复确认
        asyncio.create_task(send_data(b"ACK from RPi"))
    
    # 发送数据到PC（主动推送）
    async def send_data(data: bytes):
        await server.notify(char_tx, data)
        print(f"已发送数据: {data.decode('utf-8')}")
    
    # 保持运行
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    print("test")
    asyncio.run(main())