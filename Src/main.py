import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import asyncio
import threading
from gui import MainWindow
from ble_manager import BleManager
from socket_manager import SocketManager
from config import Config
from loguru import logger

class DGLabController:
    def __init__(self):
        # 设置日志
        logger.add("log.log", format="{time} {level} {message}", level="DEBUG")
        
        self.app = QApplication(sys.argv)
        self.config = Config()
        self.ble_manager = BleManager()
        self.socket_manager = SocketManager()
        
        # 创建主窗口
        self.window = MainWindow(self.ble_manager, self.socket_manager, self.config)
        
        # 连接信号和槽
        self._connect_signals()
        
    def _connect_signals(self):
        """连接所有信号和槽"""
        # Socket管理器信号
        self.socket_manager.connection_changed.connect(self.window.update_connection_status)
        self.socket_manager.strength_received.connect(self.window.update_strength)
        self.socket_manager.message_received.connect(self.window.add_log_message)
        
        # 蓝牙管理器信号
        self.ble_manager.connection_changed.connect(self.window.update_ble_status)
        self.ble_manager.strength_updated.connect(self.window.update_ble_strength)
        self.ble_manager.message_received.connect(self.window.add_log_message)
        
        # 界面信号
        self.window.connect_socket.connect(self.socket_manager.connect)
        self.window.disconnect_socket.connect(self.socket_manager.disconnect)
        def _connect_ble_async(device_address):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.ble_manager.connect_device(device_address))

        self.window.connect_ble.connect(lambda device_address: threading.Thread(target=_connect_ble_async, args=(device_address,)).start())
        self.window.disconnect_ble.connect(self.ble_manager.disconnect)
        self.window.set_strength_limit.connect(self.ble_manager.set_strength_limit)
        self.window.send_strength_command.connect(self.socket_manager.send_strength_command)
        
    def run(self):
        """运行应用程序"""
        self.window.show()
        return self.app.exec_()

if __name__ == "__main__":
    # 处理Qt高DPI缩放
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    controller = DGLabController()
    sys.exit(controller.run())