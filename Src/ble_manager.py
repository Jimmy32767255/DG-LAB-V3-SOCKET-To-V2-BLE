from PyQt5.QtCore import QObject, pyqtSignal
from loguru import logger
import asyncio
import pydglab
from pydglab import model_v2
from PyQt5.QtCore import QObject, pyqtSignal

class BleManager(QObject):
    connection_changed = pyqtSignal(bool, str)  # connected, status_text
    strength_updated = pyqtSignal(int, int)     # channel_a, channel_b
    message_received = pyqtSignal(str) # 接收消息信号
    
    def __init__(self):
        super().__init__()
        self.dglab = None
        self.device_address = None
        self.connected = False
        self.max_strength_a = 30
        self.max_strength_b = 30
        self.current_strength_a = 0
        self.current_strength_b = 0
        
    async def scan_devices(self):
        """扫描蓝牙设备"""
        try:
            logger.info("扫描蓝牙设备")
            # 实际扫描逻辑
            devices_raw = await pydglab.bthandler_v2.scan()
            devices = [device[0] for device in devices_raw] # 提取设备地址
            if devices:
                logger.info(f"扫描到蓝牙设备: {devices}")
            else:
                logger.warning("未扫描到任何蓝牙设备")
            return devices
        except Exception as e:
            logger.error(f"扫描蓝牙设备失败: {e}")
            return []

    async def connect_device(self, device_address: str):
        """连接蓝牙设备"""
        try:
            self.device_address = device_address
            self.dglab = pydglab.dglab(address=device_address)
            try:
                await self.dglab.create()
                # 只在成功连接后更新状态
                if self.dglab and self.dglab.is_connected:
                    self.connected = True
                    self.connection_changed.emit(True, "已连接")
                    self.message_received.emit(f"已连接到蓝牙设备: {device_address}")
                    # 开始监听强度变化
                    asyncio.create_task(self.monitor_strength())
                else:
                    raise Exception("DGLAB设备连接失败或未连接")
            except Exception as e:
                if "Unknown device" in str(e):
                    # 尝试获取并打印服务UUID，以便调试
                    if self.dglab and hasattr(self.dglab, 'client') and self.dglab.client.is_connected:
                        try:
                            services = self.dglab.client.services
                            service_uuids = [s.uuid for s in services]
                            logger.error(f"连接DGLAB设备失败: Unknown device. 设备地址: {self.device_address}, 扫描到的服务UUID: {service_uuids}")
                        except Exception as inner_e:
                            logger.error(f"连接DGLAB设备失败: Unknown device. 设备地址: {self.device_address}, 获取服务UUID失败: {inner_e}")
                    else:
                        logger.error(f"连接DGLAB设备失败: Unknown device. 设备地址: {self.device_address}, 无法获取服务UUID (客户端未连接或dglab对象无效)")
                else:
                    logger.error(f"连接DGLAB设备失败: {e}")
                self.connected = False
                self.connection_changed.emit(False, f"连接失败: {e}")
                self.message_received.emit(f"连接DGLAB设备失败: {e}")
                return # 连接失败，直接返回
        except Exception as e:
            logger.error(f"连接蓝牙设备失败: {e}")
            self.connected = False
            self.connection_changed.emit(False, f"连接失败: {e}")
        
    def disconnect(self):
        """断开蓝牙连接"""
        if self.dglab:
            def run_disconnect():
                asyncio.run(self.dglab.close())
            import threading
            disconnect_thread = threading.Thread(target=run_disconnect)
            disconnect_thread.start()
            self.dglab = None  # Set to None after the thread starts
        self.connected = False
        self.connection_changed.emit(False, "已断开")
        logger.info("蓝牙连接已断开")
        
    async def monitor_strength(self):
        """监控强度变化"""
        while self.connected:
            try:
                # 获取当前强度并更新
                if not self.dglab or not self.dglab.is_connected:
                    logger.warning("DGLAB设备未初始化或未连接，跳过强度监控")
                    await asyncio.sleep(1) # 避免CPU空转
                    continue
                
                strength_a, strength_b = await self.dglab.get_strength()
                self.current_strength_a = strength_a
                self.current_strength_b = strength_b
                self.strength_updated.emit(strength_a, strength_b)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"监控强度时出错: {e}")
                break
                
    def set_strength_limit(self, max_a, max_b):
        """设置最大强度限制"""
        self.max_strength_a = max_a
        self.max_strength_b = max_b
        logger.info(f"设置最大强度: A={max_a}, B={max_b}")
        
    async def set_strength(self, channel_a, channel_b):
        """设置强度"""
        if self.connected and self.dglab:
            try:
                # 限制强度不超过最大值且不小于0
                channel_a = min(channel_a, self.max_strength_a)
                channel_a = max(0, channel_a)
                channel_b = min(channel_b, self.max_strength_b)
                channel_b = max(0, channel_b)
                
                await self.dglab.set_strength_sync(channel_a, channel_b)
                self.current_strength_a = channel_a
                self.current_strength_b = channel_b
                self.strength_updated.emit(channel_a, channel_b)
            except Exception as e:
                logger.error(f"设置强度失败: {e}")