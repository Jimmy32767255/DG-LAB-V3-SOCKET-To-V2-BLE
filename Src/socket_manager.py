from PyQt5.QtCore import QObject, pyqtSignal
import websocket
import json
import threading

class SocketManager(QObject):
    connection_changed = pyqtSignal(bool, str)  # connected, status_text
    strength_received = pyqtSignal(int, int, int, int)  # channel_a, channel_b, max_a, max_b
    message_received = pyqtSignal(str, str)     # message, level
    
    def __init__(self):
        super().__init__()
        self.ws = None
        self.connected = False
        self.client_id = ""
        self.target_id = ""
        
    def connect(self, url):
        """连接WebSocket服务器"""
        try:
            self.message_received.emit(f"正在连接服务器 {url}...", "info")
            self.connection_changed.emit(False, "连接中...")
            
            self.ws = websocket.WebSocketApp(
                url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            # 在单独线程中运行WebSocket
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
        except Exception as e:
            self.message_received.emit(f"连接失败: {str(e)}", "error")
            self.connection_changed.emit(False, f"连接失败: {str(e)}")
            
    def disconnect(self):
        """断开WebSocket连接"""
        if self.ws:
            self.ws.close()
            
        self.connected = False
        self.connection_changed.emit(False, "已断开")
        self.message_received.emit("WebSocket连接已断开", "info")
        
    def on_open(self, ws):
        """WebSocket连接打开回调"""
        self.connected = True
        self.connection_changed.emit(True, "已连接")
        self.message_received.emit("WebSocket连接已建立", "info")
        
    def on_message(self, ws, message):
        """WebSocket消息接收回调"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "heartbeat":
                self.handle_heartbeat(data)
            elif msg_type == "bind":
                self.handle_bind(data)
            elif msg_type == "msg":
                self.handle_msg(data)
            elif msg_type == "break":
                self.handle_break(data)
            elif msg_type == "error":
                self.handle_error(data)
                
            self.message_received.emit(f"收到消息: {message}", "info")
                
        except Exception as e:
            self.message_received.emit(f"处理消息时出错: {str(e)}", "error")
            
    def on_error(self, ws, error):
        """WebSocket错误回调"""
        self.message_received.emit(f"WebSocket错误: {error}", "error")
        self.connection_changed.emit(False, f"错误: {error}")
        
    def on_close(self, ws, close_status_code, close_msg):
        """WebSocket关闭回调"""
        self.connected = False
        self.connection_changed.emit(False, "连接已关闭")
        self.message_received.emit("WebSocket连接已关闭", "info")
        
    def handle_heartbeat(self, data):
        """处理心跳消息"""
        # 发送心跳响应
        response = {
            "type": "heartbeat",
            "clientId": self.client_id,
            "targetId": self.target_id,
            "message": "200"
        }
        self.send_json(response)
        
    def handle_bind(self, data):
        """处理绑定消息"""
        if data.get("message") == "targetId":
            self.target_id = data.get("clientId")
            self.message_received.emit(f"绑定到目标: {self.target_id}", "info")
            
            # 发送绑定响应
            response = {
                "type": "bind",
                "clientId": self.client_id,
                "targetId": self.target_id,
                "message": "DGLAB"
            }
            self.send_json(response)
            
    def handle_msg(self, data):
        """处理普通消息"""
        message = data.get("message", "")
        if message.startswith("strength-"):
            self.handle_strength_message(message)
            
    def handle_strength_message(self, message):
        """处理强度消息"""
        try:
            # 解析强度消息格式: strength-A+B+maxB+maxA
            parts = message.split("-")[1].split("+")
            if len(parts) >= 4:
                channel_a = int(parts[0])
                channel_b = int(parts[1])
                max_b = int(parts[2])
                max_a = int(parts[3])
                
                self.message_received.emit(f"强度更新: A={channel_a}/{max_a}, B={channel_b}/{max_b}", "info")
                self.strength_received.emit(channel_a, channel_b, max_a, max_b)
                
        except Exception as e:
            self.message_received.emit(f"解析强度消息时出错: {e}", "error")
            
    def handle_break(self, data):
        """处理连接中断消息"""
        self.message_received.emit("连接中断", "warning")
        self.disconnect()
        
    def handle_error(self, data):
        """处理错误消息"""
        error_msg = data.get("message", "未知错误")
        self.message_received.emit(f"服务器返回错误: {error_msg}", "error")
        
    def send_json(self, data):
        """发送JSON数据"""
        if self.ws and self.connected:
            try:
                self.ws.send(json.dumps(data))
            except Exception as e:
                self.message_received.emit(f"发送数据时出错: {e}", "error")
                
    def send_strength_command(self, channel, mode, value):
        """发送强度控制命令"""
        if not self.connected:
            self.message_received.emit("未连接服务器", "warning")
            return
            
        try:
            # 构建强度命令
            message = f"strength-{channel}+{mode}+{value}"
            
            data = {
                "type": "msg",
                "clientId": self.client_id,
                "targetId": self.target_id,
                "message": message
            }
            
            self.send_json(data)
            self.message_received.emit(f"发送强度命令: {message}", "info")
            
        except Exception as e:
            self.message_received.emit(f"发送强度命令失败: {str(e)}", "error")