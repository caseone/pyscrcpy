from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QListWidget, QPushButton, QVBoxLayout, QInputDialog, QMessageBox, QWidget, QMenu, QAction
from device_manager import DeviceManager
from PyQt5.QtCore import pyqtSlot
import subprocess
import os
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QDialogButtonBox

class InputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('添加设备')
        
        layout = QVBoxLayout(self)
        
        self.id_edit = QLineEdit(self)
        self.alias_edit = QLineEdit(self)
        
        layout.addWidget(QLabel('设备ID:'))
        layout.addWidget(self.id_edit)
        layout.addWidget(QLabel('备注信息:'))
        layout.addWidget(self.alias_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.device_manager = DeviceManager()
        self.init_ui()

    # 在init_ui方法中添加设置按钮
    def init_ui(self):
        self.setWindowTitle('pyscrcpy')
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.launch_scrcpy)
        
        # 添加上下文菜单
        self.list_widget.setContextMenuPolicy(3)  # 设置为CustomContextMenu
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        btn_add = QPushButton('添加设备', self)
        btn_remove = QPushButton('删除设备', self)
        btn_connect = QPushButton('连接设备', self)
        btn_disconnect = QPushButton('断开设备', self)
        btn_config = QPushButton('查看配置', self)
        btn_setting = QPushButton('全局设置', self)  # 新增设置按钮
        btn_scrcpy = QPushButton('启动Scrcpy', self)
        btn_scrcpy.clicked.connect(self.launch_scrcpy)
        
        btn_add.clicked.connect(self.add_device)
        btn_remove.clicked.connect(self.remove_device)
        btn_connect.clicked.connect(self.connect_device)
        btn_disconnect.clicked.connect(self.disconnect_device)
        btn_config.clicked.connect(self.show_config)
        btn_setting.clicked.connect(self.show_settings)
        
        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        
        # 创建水平按钮布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(btn_add)
        button_layout.addWidget(btn_remove)
        button_layout.addWidget(btn_connect)
        button_layout.addWidget(btn_disconnect)
        button_layout.addWidget(btn_config)
        button_layout.addWidget(btn_setting)
        button_layout.addWidget(btn_scrcpy)
        
        # 将按钮布局添加到主布局
        layout.addLayout(button_layout)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.update_device_list()
    
    def update_device_list(self):
        # 获取当前adb连接设备
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
            connected_devices = [line.split('\t')[0] for line in result.stdout.split('\n') if '\tdevice' in line]
        except Exception as e:
            connected_devices = []
        
        # 更新设备状态
        for device in self.device_manager.devices:
            new_status = '已连接' if device['id'] in connected_devices else '未连接'
            if device['status'] != new_status:
                self.device_manager.update_status(device['id'], new_status)
        
        # 刷新界面显示
        self.list_widget.clear()
        for device in self.device_manager.devices:
            self.list_widget.addItem(f"{device['id']} - {device['alias']} ({device['status']})")
    
    @pyqtSlot()
    def add_device(self):
        dialog = InputDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            device_id = dialog.id_edit.text().strip()
            alias = dialog.alias_edit.text().strip()
            if device_id:
                self.device_manager.add_device({
                    'id': device_id,
                    'alias': alias,
                    'status': '未连接'
                })
                self.update_device_list()
    
    def remove_device(self):
        selected = self.list_widget.currentRow()
        if selected >= 0:
            device_id = self.device_manager.devices[selected]['id']
            self.device_manager.remove_device(device_id)
            self.update_device_list()
        else:
            QMessageBox.warning(self, '警告', '请先选择要删除的设备')

    def connect_device(self):
        selected = self.list_widget.currentRow()
        if selected >= 0:
            device_id = self.device_manager.devices[selected]['id']
            try:
                result = subprocess.run(f'adb connect {device_id}', shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                output = f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                
                if result.returncode == 0:
                    self.device_manager.update_status(device_id, '已连接')
                    QMessageBox.information(self, '连接成功', f'设备连接:\n{output}')
                else:
                    QMessageBox.warning(self, '连接异常', f'设备连接异常:\n{output}')
                self.update_device_list()
            except Exception as e:
                QMessageBox.critical(self, '连接错误', f'连接过程中发生异常: {str(e)}')
        else:
            QMessageBox.warning(self, '警告', '请先选择要连接的设备')

    def delete_device(self):
        # 删除设备逻辑
        print("删除设备")

    def start_scrcpy(self):
        # 启动scrcpy逻辑
        print("启动scrcpy")
        selected = self.list_widget.currentRow()
        if selected >= 0:
            # 获取选中设备ID
            device_id = self.device_manager.devices[selected]['id']
            
            # 检查设备ID格式
            if ':' not in device_id:
                QMessageBox.warning(self, '格式错误', '设备ID必须包含端口号（例如: 127.0.0.1:5555）')
                return
            
            try:
                # 执行adb连接命令
                result = subprocess.run(f'adb connect {device_id}', shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
                # 在launch_scrcpy方法中修正设备ID获取
                device_id = self.device_manager.devices[selected]['id']
                cmd = f'scrcpy -s {device_id} {self.device_manager.global_scrcpy_params}'
                output = f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                if result.returncode == 0:
                    self.device_manager.update_status(device_id, '已连接')
                    QMessageBox.information(self, '连接成功', f'设备连接:\n{output}')
                else:
                    QMessageBox.warning(self, '连接异常', f'设备连接异常:\n{output}')
                self.update_device_list()
            except Exception as e:
                QMessageBox.critical(self, '连接错误', f'连接过程中发生异常: {str(e)}')
        else:
            QMessageBox.warning(self, '警告', '请先选择要连接的设备')

    def disconnect_device(self):
        selected = self.list_widget.currentRow()
        if selected >= 0:
            device_id = self.device_manager.devices[selected]['id']
            try:
                result = subprocess.run(f'adb disconnect {device_id}', shell=True, capture_output=True, text=True, encoding='utf-8')
                output = f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                
                if result.returncode == 0:
                    self.device_manager.update_status(device_id, '未连接')
                    QMessageBox.information(self, '断开成功', f'设备已断开连接:\n{output}')
                else:
                    QMessageBox.warning(self, '断开异常', f'设备断开异常:\n{output}')
                self.update_device_list()
            except Exception as e:
                QMessageBox.critical(self, '断开错误', f'断开过程中发生异常: {str(e)}')
        else:
            QMessageBox.warning(self, '警告', '请先选择要断开的设备')

    # 新增配置文件查看功能
    def show_config(self):
        config_path = self.device_manager.config_path
        if os.path.exists(config_path):
            os.startfile(config_path)
        else:
            QMessageBox.information(self, '提示', '配置文件尚未创建')
    
    # 新增设置对话框方法
    def show_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('全局参数设置')
        layout = QVBoxLayout()
        
        self.param_edit = QLineEdit(self.device_manager.global_scrcpy_params)
        layout.addWidget(QLabel('Scrcpy全局参数:'))
        layout.addWidget(self.param_edit)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        
        dialog.setLayout(layout)
        if dialog.exec_() == QDialog.Accepted:
            self.device_manager.global_scrcpy_params = self.param_edit.text().strip()
            self.device_manager.save_devices()

    # 修改scrcpy启动命令
    def launch_scrcpy(self):
        selected = self.list_widget.currentRow()
        device_id = self.device_manager.devices[selected]['id']
        cmd = f'scrcpy -s {device_id} {self.device_manager.global_scrcpy_params}'
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=30)
            output = f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            
            if result.returncode != 0 or 'error' in result.stderr.lower():
                QMessageBox.warning(self, '执行错误', f'scrcpy启动失败:\n{output}')
            else:
                QMessageBox.information(self, '执行成功', 'scrcpy已正常启动')
        except subprocess.TimeoutExpired:
            QMessageBox.warning(self, '超时错误', 'scrcpy启动超时')
        except Exception as e:
            QMessageBox.critical(self, '意外错误', f'发生未知错误: {str(e)}')
    
    def show_context_menu(self, pos):
        menu = QMenu()
        copy_action = QAction('复制设备ID', menu)
        connect_action = QAction('连接设备', menu)
        scrcpy_action = QAction('启动scrcpy', menu)  # 新增启动scrcpy选项
        
        copy_action.triggered.connect(self.copy_device_id)
        connect_action.triggered.connect(self.connect_device)
        scrcpy_action.triggered.connect(self.launch_scrcpy)  # 连接到启动scrcpy方法
        
        menu.addAction(copy_action)
        menu.addAction(connect_action)
        menu.addAction(scrcpy_action)  # 添加到菜单
        
        menu.exec_(self.list_widget.mapToGlobal(pos))
    
    def copy_device_id(self):
        selected = self.list_widget.currentRow()
        if selected >= 0:
            device_id = self.device_manager.devices[selected]['id']
            QApplication.clipboard().setText(device_id)
        else:
            QMessageBox.warning(self, '警告', '请先选择要复制的设备')

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())