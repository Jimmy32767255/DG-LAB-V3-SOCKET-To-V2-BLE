import asyncio
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox,
                             QSpinBox, QTextEdit, QProgressBar, QScrollArea,
                             QMessageBox)
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QDateTime

class MainWindow(QMainWindow):
    # 信号定义
    connect_socket = pyqtSignal(str)
    disconnect_socket = pyqtSignal()
    connect_ble = pyqtSignal(str)
    disconnect_ble = pyqtSignal()
    set_strength_limit = pyqtSignal(int, int)
    send_strength_command = pyqtSignal(int, str, int)  # channel, mode, value
    
    def __init__(self, ble_manager, socket_manager, config):
        super().__init__()
        self.ble_manager = ble_manager
        self.socket_manager = socket_manager
        self.config = config
        
        self.setWindowTitle("DG-Lab 控制器")
        self.setGeometry(100, 100, 1000, 700)
        
        self.init_ui()
        self.load_config()
        
    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧控制面板
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel, 1)
        
        # 右侧日志面板
        log_panel = self.create_log_panel()
        main_layout.addWidget(log_panel, 1)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
    def create_control_panel(self):
        """创建左侧控制面板"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Socket连接部分
        socket_group = self.create_socket_group()
        layout.addWidget(socket_group)
        
        # 蓝牙连接部分
        ble_group = self.create_ble_group()
        layout.addWidget(ble_group)
        
        # 强度控制部分
        strength_group = self.create_strength_group()
        layout.addWidget(strength_group)
        
        # 按钮部分
        button_group = self.create_button_group()
        layout.addWidget(button_group)
        
        layout.addStretch()
        scroll_area.setWidget(container)
        
        return scroll_area
        
    def create_socket_group(self):
        """创建Socket连接组"""
        group = QGroupBox("WebSocket 连接")
        layout = QVBoxLayout(group)
        
        # 服务器地址
        server_layout = QHBoxLayout()
        server_layout.addWidget(QLabel("服务器地址:"))
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("ws://127.0.0.1:9999/1234-123456789-12345-12345-01")
        server_layout.addWidget(self.server_input)
        layout.addLayout(server_layout)
        
        # 连接按钮
        btn_layout = QHBoxLayout()
        self.socket_connect_btn = QPushButton("连接")
        self.socket_connect_btn.clicked.connect(self.on_socket_connect)
        btn_layout.addWidget(self.socket_connect_btn)
        
        self.socket_disconnect_btn = QPushButton("断开")
        self.socket_disconnect_btn.setEnabled(False)
        self.socket_disconnect_btn.clicked.connect(self.on_socket_disconnect)
        btn_layout.addWidget(self.socket_disconnect_btn)
        layout.addLayout(btn_layout)
        
        # 状态显示
        self.socket_status = QLabel("状态: 未连接")
        layout.addWidget(self.socket_status)
        
        return group
        
    def create_ble_group(self):
        """创建蓝牙连接组"""
        group = QGroupBox("蓝牙连接")
        layout = QVBoxLayout(group)
        
        # 设备选择
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("蓝牙设备:"))
        self.ble_combo = QComboBox()
        device_layout.addWidget(self.ble_combo)
        
        self.ble_refresh_btn = QPushButton("刷新")
        self.ble_refresh_btn.clicked.connect(self.refresh_ble_devices)
        device_layout.addWidget(self.ble_refresh_btn)
        layout.addLayout(device_layout)
        
        # 连接按钮
        btn_layout = QHBoxLayout()
        self.ble_connect_btn = QPushButton("连接")
        self.ble_connect_btn.clicked.connect(self.on_ble_connect)
        btn_layout.addWidget(self.ble_connect_btn)
        
        self.ble_disconnect_btn = QPushButton("断开")
        self.ble_disconnect_btn.setEnabled(False)
        self.ble_disconnect_btn.clicked.connect(self.on_ble_disconnect)
        btn_layout.addWidget(self.ble_disconnect_btn)
        layout.addLayout(btn_layout)
        
        # 状态显示
        self.ble_status = QLabel("状态: 未连接")
        layout.addWidget(self.ble_status)
        
        return group
        
    def create_strength_group(self):
        """创建强度控制组"""
        group = QGroupBox("强度控制")
        layout = QVBoxLayout(group)
        
        # 通道A
        channel_a_group = QGroupBox("通道 A")
        channel_a_layout = QVBoxLayout(channel_a_group)
        
        a_strength_layout = QHBoxLayout()
        a_strength_layout.addWidget(QLabel("当前强度:"))
        self.strength_a_label = QLabel("0")
        a_strength_layout.addWidget(self.strength_a_label)
        
        self.strength_a_bar = QProgressBar()
        self.strength_a_bar.setRange(0, 100)
        self.strength_a_bar.setValue(0)
        a_strength_layout.addWidget(self.strength_a_bar)
        channel_a_layout.addLayout(a_strength_layout)
        
        # 通道A控制按钮
        a_btn_layout = QHBoxLayout()
        self.a_minus_btn = QPushButton("-")
        self.a_minus_btn.clicked.connect(lambda: self.on_strength_change(1, 0, 5))
        a_btn_layout.addWidget(self.a_minus_btn)
        
        self.a_plus_btn = QPushButton("+")
        self.a_plus_btn.clicked.connect(lambda: self.on_strength_change(1, "1", 5))
        a_btn_layout.addWidget(self.a_plus_btn)
        
        self.a_zero_btn = QPushButton("归零")
        self.a_zero_btn.clicked.connect(lambda: self.on_strength_change(1, "2", 0))
        a_btn_layout.addWidget(self.a_zero_btn)
        channel_a_layout.addLayout(a_btn_layout)
        
        layout.addWidget(channel_a_group)
        
        # 通道B
        channel_b_group = QGroupBox("通道 B")
        channel_b_layout = QVBoxLayout(channel_b_group)
        
        b_strength_layout = QHBoxLayout()
        b_strength_layout.addWidget(QLabel("当前强度:"))
        self.strength_b_label = QLabel("0")
        b_strength_layout.addWidget(self.strength_b_label)
        
        self.strength_b_bar = QProgressBar()
        self.strength_b_bar.setRange(0, 100)
        self.strength_b_bar.setValue(0)
        b_strength_layout.addWidget(self.strength_b_bar)
        channel_b_layout.addLayout(b_strength_layout)
        
        # 通道B控制按钮
        b_btn_layout = QHBoxLayout()
        self.b_minus_btn = QPushButton("-")
        self.b_minus_btn.clicked.connect(lambda: self.on_strength_change(2, 0, 5))
        b_btn_layout.addWidget(self.b_minus_btn)
        
        self.b_plus_btn = QPushButton("+")
        self.b_plus_btn.clicked.connect(lambda: self.on_strength_change(2, 1, 5))
        b_btn_layout.addWidget(self.b_plus_btn)
        
        self.b_zero_btn = QPushButton("归零")
        self.b_zero_btn.clicked.connect(lambda: self.on_strength_change(2, 2, 0))
        b_btn_layout.addWidget(self.b_zero_btn)
        channel_b_layout.addLayout(b_btn_layout)
        
        layout.addWidget(channel_b_group)
        
        # 最大强度设置
        max_strength_layout = QHBoxLayout()
        max_strength_layout.addWidget(QLabel("最大强度A:"))
        self.max_a_spin = QSpinBox()
        self.max_a_spin.setRange(0, 100)
        self.max_a_spin.setValue(30)
        max_strength_layout.addWidget(self.max_a_spin)
        
        max_strength_layout.addWidget(QLabel("最大强度B:"))
        self.max_b_spin = QSpinBox()
        self.max_b_spin.setRange(0, 100)
        self.max_b_spin.setValue(30)
        max_strength_layout.addWidget(self.max_b_spin)
        
        self.set_max_btn = QPushButton("设置")
        self.set_max_btn.clicked.connect(self.on_set_max_strength)
        max_strength_layout.addWidget(self.set_max_btn)
        layout.addLayout(max_strength_layout)
        
        return group
        
    def create_button_group(self):
        """创建按钮组"""
        group = QGroupBox("操作")
        layout = QHBoxLayout(group)
        
        self.save_btn = QPushButton("保存配置")
        self.save_btn.clicked.connect(self.save_config)
        layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton("加载配置")
        self.load_btn.clicked.connect(self.load_config)
        layout.addWidget(self.load_btn)
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_all)
        layout.addWidget(self.reset_btn)
        
        return group
        
    def create_log_panel(self):
        """创建右侧日志面板"""
        group = QGroupBox("日志")
        layout = QVBoxLayout(group)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(400)
        layout.addWidget(self.log_view)
        
        # 状态信息
        status_group = QGroupBox("状态信息")
        status_layout = QVBoxLayout(status_group)
        
        self.status_info = QTextEdit()
        self.status_info.setReadOnly(True)
        self.status_info.setMaximumHeight(200)
        status_layout.addWidget(self.status_info)
        
        layout.addWidget(status_group)
        
        return group
        
    def on_socket_connect(self):
        """处理Socket连接按钮点击"""
        server_url = self.server_input.text().strip()
        if not server_url:
            QMessageBox.warning(self, "警告", "请输入服务器地址")
            return
            
        self.config.set("socket_server", server_url)
        self.connect_socket.emit(server_url)
        
    def on_socket_disconnect(self):
        """处理Socket断开按钮点击"""
        self.disconnect_socket.emit()
        
    def on_ble_connect(self):
        """处理蓝牙连接按钮点击"""
        if self.ble_combo.count() == 0:
            QMessageBox.warning(self, "警告", "没有可用的蓝牙设备，请先刷新")
            return
            
        device_address = self.ble_combo.currentData()
        if device_address:
            # 在单独的线程中运行异步连接
            def run_connect():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.ble_manager.connect_device(str(device_address)))

            import threading
            connect_thread = threading.Thread(target=run_connect)
            self.connect_ble.emit(str(device_address))
            connect_thread.start()
            
    def on_ble_disconnect(self):
        """处理蓝牙断开按钮点击"""
        self.disconnect_ble.emit()
        
    def on_set_max_strength(self):
        """处理设置最大强度按钮点击"""
        max_a = self.max_a_spin.value()
        max_b = self.max_b_spin.value()
        self.set_strength_limit.emit(max_a, max_b)
        
    def on_strength_change(self, channel, mode, value):
        """处理强度变化"""
        self.send_strength_command.emit(channel, str(mode), value)
        
    def refresh_ble_devices(self):
        """刷新蓝牙设备列表"""
        self.ble_refresh_btn.setEnabled(False)
        self.ble_combo.clear()
        self.ble_combo.addItem("扫描中...")
        
        # 在单独的线程中运行异步扫描
        def run_scan():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            devices = loop.run_until_complete(self.ble_manager.scan_devices())
            self.populate_ble_devices(devices)
            self.ble_refresh_btn.setEnabled(True)

        import threading
        scan_thread = threading.Thread(target=run_scan)
        scan_thread.start()

    def populate_ble_devices(self, devices):
        """填充蓝牙设备列表"""
        self.ble_combo.clear()
        
        if not devices:
            self.ble_combo.addItem("未找到设备", "")
            return
            
        for device_address in devices:
            self.ble_combo.addItem(device_address, device_address)
            
    def update_connection_status(self, connected, status_text):
        """更新Socket连接状态"""
        self.socket_connect_btn.setEnabled(not connected)
        self.socket_disconnect_btn.setEnabled(connected)
        self.socket_status.setText(f"状态: {status_text}")
        
    def update_ble_status(self, connected, status_text):
        """更新蓝牙连接状态"""
        self.ble_connect_btn.setEnabled(not connected)
        self.ble_disconnect_btn.setEnabled(connected)
        self.ble_status.setText(f"状态: {status_text}")
        
    def update_strength(self, channel_a, channel_b, max_a, max_b):
        """更新强度显示"""
        self.strength_a_bar.setValue(int(channel_a / max_a * 100) if max_a > 0 else 0)
        self.strength_b_bar.setValue(int(channel_b / max_b * 100) if max_b > 0 else 0)
        self.strength_a_label.setText(f"{channel_a}/{max_a}")
        self.strength_b_label.setText(f"{channel_b}/{max_b}")
        
    def update_ble_strength(self, channel_a, channel_b):
        """更新蓝牙强度显示"""
        # 可以在这里添加额外的蓝牙强度显示逻辑
        pass
        
    def add_log_message(self, message, level="info"):
        """添加日志消息"""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        if level == "error":
            formatted_message = f"<font color='red'>[{timestamp}] {message}</font>"
        elif level == "warning":
            formatted_message = f"<font color='orange'>[{timestamp}] {message}</font>"
        else:
            formatted_message = f"[{timestamp}] {message}"
            
        self.log_view.append(formatted_message)
        
        # 自动滚动到底部
        scrollbar = self.log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def save_config(self):
        """保存配置"""
        try:
            self.config.set("max_strength_a", self.max_a_spin.value())
            self.config.set("max_strength_b", self.max_b_spin.value())
            self.config.set("socket_server", self.server_input.text())
            
            self.add_log_message("配置已保存", "info")
            QMessageBox.information(self, "成功", "配置已保存")
        except Exception as e:
            self.add_log_message(f"保存配置失败: {str(e)}", "error")
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
            
    def load_config(self):
        """加载配置"""
        try:
            self.max_a_spin.setValue(self.config.get("max_strength_a", 30))
            self.max_b_spin.setValue(self.config.get("max_strength_b", 30))
            self.server_input.setText(self.config.get("socket_server", ""))
            
            self.add_log_message("配置已加载", "info")
        except Exception as e:
            self.add_log_message(f"加载配置失败: {str(e)}", "error")
            
    def reset_all(self):
        """重置所有设置"""
        reply = QMessageBox.question(self, "确认", "确定要重置所有设置吗？",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.max_a_spin.setValue(30)
            self.max_b_spin.setValue(30)
            self.server_input.clear()
            self.log_view.clear()
            self.add_log_message("所有设置已重置", "info")