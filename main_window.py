from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QListWidget, QPushButton, QVBoxLayout, QInputDialog, QMessageBox, QWidget, QMenu, QAction
from device_manager import DeviceManager
from PyQt5.QtCore import pyqtSlot, QProcess, QTimer
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
        
        # 新增代码：自动添加网络设备到配置文件
        for dev_id in connected_devices:
            # 检查是否已存在
            if not any(d['id'] == dev_id for d in self.device_manager.devices):
                self.device_manager.add_device({
                    'id': dev_id,
                    'alias': dev_id,
                    'status': '已连接'
                })
        
        # 刷新界面显示
        self.list_widget.clear()
        max_id_len = max(len(d['id']) for d in self.device_manager.devices) if self.device_manager.devices else 0
        max_alias_len = max(len(d['alias']) for d in self.device_manager.devices) if self.device_manager.devices else 0
        for device in self.device_manager.devices:
            # iterm = f"{device['id']} - {device['alias']} ({device['status']})"
            # item = "{:<20} {:<20} {:<20}".format(device['id'], "-"+device['alias'], device['status'])
            item = f"{device['id'].ljust(max(max_id_len, 20))} - {device['alias'].ljust(max(max_alias_len, 15))} {device['status']}"
            # print(item)
            self.list_widget.addItem(item)
    
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
        if selected < 0:
            QMessageBox.warning(self, '警告', '请先选择要启动的设备')
            return
            
        device_id = self.device_manager.devices[selected]['id']
        cmd = f'scrcpy -s {device_id} {self.device_manager.global_scrcpy_params}'
        
        # 使用QProcess异步执行
        self.process = QProcess(self)
        self.process.started.connect(lambda: self.statusBar().showMessage("正在启动scrcpy..."))
        self.process.finished.connect(lambda: self.statusBar().showMessage("scrcpy已退出"))
        self.process.errorOccurred.connect(self.handle_scrcpy_error)
        
        try:
            # 分离命令行参数
            args = cmd.split()
            program = args[0]
            args = args[1:]
            
            self.process.start(program, args)
            
            # 添加超时检测（30秒）
            QTimer.singleShot(30000, lambda: (
                self.process.kill() if self.process.state() == QProcess.Running else None,
                QMessageBox.warning(self, '超时错误', 'scrcpy启动超时')
            ))
        except Exception as e:
            QMessageBox.critical(self, '启动错误', f'无法启动进程: {str(e)}')
    
    def handle_scrcpy_error(self, error):
        error_msg = {
            QProcess.FailedToStart: "进程无法启动",
            QProcess.Crashed: "进程意外崩溃",
            QProcess.Timedout: "进程超时",
            QProcess.WriteError: "写入错误",
            QProcess.ReadError: "读取错误",
            QProcess.UnknownError: "未知错误"
        }.get(error, "未知错误")
        QMessageBox.warning(self, '进程错误', f'scrcpy运行异常: {error_msg}')
    def show_context_menu(self, pos):
        menu = QMenu()
        copy_action = QAction('复制设备ID', menu)
        connect_action = QAction('连接设备', menu)
        scrcpy_action = QAction('启动scrcpy', menu)
        modify_action = QAction('修改别名', menu)
        adb_shell_action = QAction('ADB Shell', menu)

        copy_action.triggered.connect(self.copy_device_id)
        connect_action.triggered.connect(self.connect_device)
        scrcpy_action.triggered.connect(self.launch_scrcpy)
        modify_action.triggered.connect(self.modify_alias)
        adb_shell_action.triggered.connect(self.open_adb_shell)  # 连接信号

        menu.addAction(copy_action)
        menu.addAction(connect_action)
        menu.addAction(scrcpy_action)
        menu.addAction(adb_shell_action)
        menu.addAction(modify_action)

        
        menu.exec_(self.list_widget.mapToGlobal(pos))

    def open_adb_shell(self):  # 新增处理方法
        selected = self.list_widget.currentRow()
        if selected >= 0:
            device_id = self.device_manager.devices[selected]['id']
            try:
                # 使用Windows start命令创建独立控制台窗口
                subprocess.Popen(
                    f'start cmd /k adb -s {device_id} shell',
                    shell=True,
                    # creationflags=subprocess.CREATE_NEW_CONSOLE,
                    stdin=subprocess.DEVNULL,    # 防止输入流阻塞
                    stdout=subprocess.DEVNULL,   # 忽略标准输出
                    stderr=subprocess.DEVNULL    # 忽略错误输出
                )
            except Exception as e:
                error_msg = f'错误详情：{str(e)}'
                QMessageBox.critical(
                    self, '错误',
                    f'ADB Shell启动失败！\n{error_msg}\n'
                    '常见问题排查：\n'
                    '1. 确认adb.exe在PATH环境变量中\n'
                    '2. 设备需要先成功连接\n'
                    '3. 允许程序通过防火墙\n'
                    '4. 尝试管理员身份运行程序'
                )
        else:
            QMessageBox.warning(self, '警告', '请先选择设备')

    def modify_alias(self):
        selected = self.list_widget.currentRow()
        if selected >= 0:
            device_id = self.device_manager.devices[selected]['id']
            current_alias = self.device_manager.devices[selected]['alias']
            
            dialog = InputDialog(self)
            dialog.setWindowTitle('修改设备别名')
            dialog.id_edit.setText(device_id)
            dialog.id_edit.setEnabled(False)  # 禁用ID编辑
            dialog.alias_edit.setText(current_alias)
            
            if dialog.exec_() == QDialog.Accepted:
                new_alias = dialog.alias_edit.text().strip()
                self.device_manager.update_alias(device_id, new_alias)
                self.update_device_list()
        else:
            QMessageBox.warning(self, '警告', '请先选择要修改的设备')

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