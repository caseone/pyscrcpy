import json
import os
from PyQt5.QtWidgets import QMessageBox

class DeviceManager:
    def __init__(self):
        # 修改配置文件名
        self.config_path = 'pyscrcpy.json'
        self.devices = []
        self.global_scrcpy_params = ''
        self.load_devices()
    
    def add_device(self, device):
        if not any(d['id'] == device['id'] for d in self.devices):
            self.devices.append({
                'id': device['id'],
                'alias': device.get('alias', ''),

                'status': device.get('status', '未连接'),
                'last_connect': ''
            })
            self.save_devices()

    def remove_device(self, device_id):
        self.devices = [d for d in self.devices if d['id'] != device_id]
        self.save_devices()

    def update_status(self, device_id, status):
        for device in self.devices:
            if device['id'] == device_id:
                device['status'] = status
        self.save_devices()

    def load_devices(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    # 兼容旧版列表格式配置文件
                    if isinstance(config_data, list):
                        self.devices = config_data
                        self.global_scrcpy_params = ''
                    else:
                        self.devices = config_data.get('devices', [])
                        self.global_scrcpy_params = config_data.get('global_scrcpy_params', '')  # 加载全局参数
            else:
                self.devices = []
        except json.JSONDecodeError:
            QMessageBox.critical(None, '配置错误', '配置文件格式错误')
        except Exception as e:
            QMessageBox.critical(None, '配置错误', f'加载配置文件失败: {str(e)}')

    def save_devices(self):
        try:
            config_data = {
                'devices': self.devices,
                'global_scrcpy_params': self.global_scrcpy_params  # 保存全局参数
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(None, '配置错误', f'保存配置文件失败: {str(e)}')