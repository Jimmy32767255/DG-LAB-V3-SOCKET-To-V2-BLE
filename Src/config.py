import json
import os
from loguru import logger

class Config:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                return {}
        else:
            return {}
            
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            logger.info("配置文件已保存")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            
    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """设置配置值"""
        self.config[key] = value
        self.save_config()
        
    def remove(self, key):
        """删除配置值"""
        if key in self.config:
            del self.config[key]
            self.save_config()