# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout, QInputDialog, QMessageBox, QWidget, QMenu, QAction, QGroupBox, QFileDialog
from device_manager import DeviceManager
from PyQt5.QtCore import pyqtSlot, QProcess, QTimer, Qt
import subprocess
import os
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QDialogButtonBox
from PyQt5.QtWidgets import QHeaderView

class InputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('添加设备')

        layout = QVBoxLayout(self)

        self.id_edit = QLineEdit(self)
        self.alias_edit = QLineEdit(self)

        layout.addWidget(QLabel('设备 ID:'))
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
        self.resize(980, 680)
        self._adb_processes = []
        self._sort_state = {'col': -1, 'order': None}

        self.list_widget = QTableWidget()
        self.list_widget.setColumnCount(3)
        self.list_widget.setHorizontalHeaderLabels(['设备 ID', '别名', '状态'])
        self.list_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.list_widget.setColumnWidth(0, 200)
        self.list_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.list_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.list_widget.setSelectionBehavior(self.list_widget.SelectRows)
        self.list_widget.setEditTriggers(self.list_widget.NoEditTriggers)
        self.list_widget.setSortingEnabled(False)
        self.list_widget.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        self.list_widget.cellDoubleClicked.connect(lambda _row, _col: self.launch_scrcpy())

        self.list_widget.setContextMenuPolicy(3)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

        btn_add = QPushButton('添加设备', self)
        btn_remove = QPushButton('删除设备', self)
        btn_connect = QPushButton('连接设备', self)
        btn_disconnect = QPushButton('断开设备', self)
        btn_config = QPushButton('查看配置', self)
        btn_setting = QPushButton('全局设置', self)
        btn_scrcpy = QPushButton('启动 Scrcpy', self)
        btn_scrcpy.clicked.connect(self.launch_scrcpy)

        btn_add.clicked.connect(self.add_device)
        btn_remove.clicked.connect(self.remove_device)
        btn_connect.clicked.connect(self.connect_device)
        btn_disconnect.clicked.connect(self.disconnect_device)
        btn_upload.clicked.connect(self.upload_file)
        btn_config.clicked.connect(self.show_config)
        btn_setting.clicked.connect(self.show_settings)

        list_container = QWidget()
        list_layout = QVBoxLayout()
        list_layout.addWidget(self.list_widget)
        list_container.setLayout(list_layout)

        action_container = QWidget()
        action_layout = QVBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)

        device_group = QGroupBox('设备')
        device_layout = QVBoxLayout()
        device_layout.addWidget(btn_add)
        device_layout.addWidget(btn_remove)
        device_layout.addWidget(btn_connect)
        device_layout.addWidget(btn_disconnect)
        device_layout.addWidget(btn_upload)
        device_group.setLayout(device_layout)

        config_group = QGroupBox('配置')
        config_layout = QVBoxLayout()
        config_layout.addWidget(btn_config)
        config_layout.addWidget(btn_setting)
        config_group.setLayout(config_layout)

        scrcpy_group = QGroupBox('投屏')
        scrcpy_layout = QVBoxLayout()
        scrcpy_layout.addWidget(btn_scrcpy)
        scrcpy_group.setLayout(scrcpy_layout)

        action_layout.addWidget(device_group)
        action_layout.addWidget(config_group)
        action_layout.addWidget(scrcpy_group)
        action_layout.addStretch(1)
        action_container.setLayout(action_layout)
        action_container.setMinimumWidth(150)

        main_layout = QHBoxLayout()
        main_layout.addWidget(list_container, 4)
        main_layout.addWidget(action_container, 1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        self.update_device_list()

    def on_header_clicked(self, section):
        if self._sort_state['col'] != section:
            self._sort_state['col'] = section
            self._sort_state['order'] = Qt.AscendingOrder
        else:
            if self._sort_state['order'] == Qt.AscendingOrder:
                self._sort_state['order'] = Qt.DescendingOrder
            elif self._sort_state['order'] == Qt.DescendingOrder:
                self._sort_state['order'] = None
            else:
                self._sort_state['order'] = Qt.AscendingOrder

        self.update_device_list()

    def _run_adb_command(self, args, timeout_ms, on_done, show_errors=True):
        process = QProcess(self)
        process.setProgram(args[0])
        process.setArguments(args[1:])

        timer = QTimer(process)
        timer.setSingleShot(True)
        state = {'timed_out': False}

        def handle_timeout():
            state['timed_out'] = True
            if process.state() == QProcess.Running:
                process.kill()

        def cleanup():
            if process in self._adb_processes:
                self._adb_processes.remove(process)
            process.deleteLater()

        def handle_finish(exit_code, exit_status):
            timer.stop()
            stdout = bytes(process.readAllStandardOutput()).decode('utf-8', errors='ignore')
            stderr = bytes(process.readAllStandardError()).decode('utf-8', errors='ignore')
            on_done(exit_code, stdout, stderr, state['timed_out'])
            cleanup()

        def handle_error(_error):
            timer.stop()
            if show_errors:
                QMessageBox.warning(self, 'ADB ??', 'ADB ?????????? ADB ?????? PATH?')
            cleanup()

        process.finished.connect(handle_finish)
        process.errorOccurred.connect(handle_error)
        timer.timeout.connect(handle_timeout)

        self._adb_processes.append(process)
        process.start()
        timer.start(timeout_ms)

    def update_device_list(self):
        def handle_devices(exit_code, stdout, _stderr, timed_out):
            if timed_out or exit_code != 0:
                connected_devices = []
            else:
                connected_devices = [
                    line.split('\t')[0]
                    for line in stdout.split('\n')
                    if '\tdevice' in line
                ]

            connected_label = '已连接'
            disconnected_label = '未连接'

            for device in self.device_manager.devices:
                new_status = connected_label if device['id'] in connected_devices else disconnected_label
                if device['status'] != new_status:
                    self.device_manager.update_status(device['id'], new_status)

            for dev_id in connected_devices:
                if not any(d['id'] == dev_id for d in self.device_manager.devices):
                    self.device_manager.add_device({
                        'id': dev_id,
                        'alias': dev_id,
                        'status': connected_label
                    })

            self.list_widget.setRowCount(len(self.device_manager.devices))
            for row, device in enumerate(self.device_manager.devices):
                self.list_widget.setItem(row, 0, QTableWidgetItem(device['id']))
                self.list_widget.setItem(row, 1, QTableWidgetItem(device['alias']))
                self.list_widget.setItem(row, 2, QTableWidgetItem(device['status']))

            if self._sort_state['order'] is None:
                self.list_widget.setSortingEnabled(False)
            else:
                self.list_widget.setSortingEnabled(True)
                self.list_widget.sortItems(self._sort_state['col'], self._sort_state['order'])

        self._run_adb_command(['adb', 'devices'], 3000, handle_devices, show_errors=False)

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
                    'status': '???'
                })
                self.update_device_list()
    
    def remove_device(self):
        selected = self.list_widget.currentRow()
        if selected >= 0:
            device_id = self.device_manager.devices[selected]['id']
            self.device_manager.remove_device(device_id)
            self.update_device_list()
        else:
            QMessageBox.warning(self, '警告', '请先选择要删除的设备。')

    def connect_device(self):
        selected = self.list_widget.currentRow()
        if selected >= 0:
            device_id = self.device_manager.devices[selected]['id']

            def handle_connect(exit_code, stdout, stderr, timed_out):
                output = f"stdout:\n{stdout}\nstderr:\n{stderr}"
                if timed_out:
                    QMessageBox.warning(self, '连接超时', 'ADB 连接超时，请检查设备或网络。')
                elif exit_code == 0:
                    self.device_manager.update_status(device_id, '已连接')
                    QMessageBox.information(self, '连接成功', f'设备已连接:\n{output}')
                else:
                    QMessageBox.warning(self, '连接失败', f'ADB 连接失败:\n{output}')
                self.update_device_list()

            self._run_adb_command(['adb', 'connect', device_id], 8000, handle_connect)
        else:
            QMessageBox.warning(self, '警告', '请先选择要连接的设备。')

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
                    self.device_manager.update_status(device_id, 'Disconnected')
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

            def handle_disconnect(exit_code, stdout, stderr, timed_out):
                output = f"stdout:\n{stdout}\nstderr:\n{stderr}"
                if timed_out:
                    QMessageBox.warning(self, '断开超时', 'ADB 断开超时，请检查设备或网络。')
                elif exit_code == 0:
                    self.device_manager.update_status(device_id, '未连接')
                    QMessageBox.information(self, '断开成功', f'设备已断开:\n{output}')
                else:
                    QMessageBox.warning(self, '断开失败', f'ADB 断开失败:\n{output}')
                self.update_device_list()

            self._run_adb_command(['adb', 'disconnect', device_id], 8000, handle_disconnect)
        else:
            QMessageBox.warning(self, '警告', '请先选择要断开的设备。')

    def upload_file(self):
        selected = self.list_widget.currentRow()
        if selected < 0:
            QMessageBox.warning(self, '警告', '请先选择要上传的设备。')
            return

        start_dir = self.device_manager.last_local_dir or ''
        local_file, _ = QFileDialog.getOpenFileName(self, '选择文件', start_dir)
        if not local_file:
            return

        import os
        self.device_manager.last_local_dir = os.path.dirname(local_file)

        default_path = self.device_manager.default_push_path or '/sdcard/Download/'
        target_path, ok = QInputDialog.getText(
            self,
            '上传目标路径',
            '请输入手机上的目标目录或完整文件路径:\n例: /sdcard/Download/ 或 /data/local/tmp/app.apk',
            text=default_path
        )
        if not ok or not target_path.strip():
            return

        target_path = target_path.strip()
        self.device_manager.default_push_path = target_path
        self.device_manager.save_devices()

        if target_path.endswith('/'):
            remote_path = target_path + os.path.basename(local_file)
        else:
            remote_path = target_path

        device_id = self.device_manager.devices[selected]['id']

        def handle_push(exit_code, stdout, stderr, timed_out):
            output = f"stdout:\n{stdout}\nstderr:\n{stderr}"
            if timed_out:
                QMessageBox.warning(self, '上传超时', 'ADB push 超时，请检查设备或网络。')
            elif exit_code == 0:
                QMessageBox.information(self, '上传成功', f'文件已上传:\n{remote_path}\n\n{output}')
            else:
                QMessageBox.warning(self, '上传失败', f'ADB push 失败:\n{output}')

        self._run_adb_command(['adb', '-s', device_id, 'push', local_file, remote_path], 15000, handle_push)

    def show_config(self):
        config_path = self.device_manager.config_path
        if os.path.exists(config_path):
            os.startfile(config_path)
        else:
            QMessageBox.information(self, '提示', '配置文件尚未创建。')

    def show_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('全局参数设置')
        layout = QVBoxLayout()

        self.param_edit = QLineEdit(self.device_manager.global_scrcpy_params)
        layout.addWidget(QLabel('Scrcpy 全局参数:'))
        layout.addWidget(self.param_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        dialog.setLayout(layout)
        if dialog.exec_() == QDialog.Accepted:
            self.device_manager.global_scrcpy_params = self.param_edit.text().strip()
            self.device_manager.save_devices()

    def launch_scrcpy(self):
        selected = self.list_widget.currentRow()
        if selected < 0:
            QMessageBox.warning(self, '警告', '请先选择要启动的设备。')
            return

        device_id = self.device_manager.devices[selected]['id']
        cmd = f'scrcpy -s {device_id} {self.device_manager.global_scrcpy_params}'

        self.scrcpy_process = QProcess(self)
        self.scrcpy_process.started.connect(lambda: self.statusBar().showMessage("正在启动 scrcpy..."))
        self.scrcpy_process.finished.connect(lambda: self.statusBar().showMessage("scrcpy 已退出"))
        self.scrcpy_process.errorOccurred.connect(self.handle_scrcpy_error)

        try:
            args = cmd.split()
            program = args[0]
            args = args[1:]

            self.scrcpy_process.start(program, args)
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
        QMessageBox.warning(self, '进程错误', f'scrcpy 运行异常: {error_msg}')

    def show_context_menu(self, pos):
        menu = QMenu()
        copy_action = QAction('复制设备 ID', menu)
        connect_action = QAction('连接设备', menu)
        scrcpy_action = QAction('启动 scrcpy', menu)
        upload_action = QAction('上传文件', menu)
        modify_action = QAction('修改别名', menu)
        adb_shell_action = QAction('ADB Shell', menu)

        copy_action.triggered.connect(self.copy_device_id)
        connect_action.triggered.connect(self.connect_device)
        scrcpy_action.triggered.connect(self.launch_scrcpy)
        upload_action.triggered.connect(self.upload_file)
        modify_action.triggered.connect(self.modify_alias)
        adb_shell_action.triggered.connect(self.open_adb_shell)

        menu.addAction(copy_action)
        menu.addAction(connect_action)
        menu.addAction(scrcpy_action)
        menu.addAction(upload_action)
        menu.addAction(adb_shell_action)
        menu.addAction(modify_action)

        menu.exec_(self.list_widget.viewport().mapToGlobal(pos))

    def open_adb_shell(self):
        selected = self.list_widget.currentRow()
        if selected >= 0:
            device_id = self.device_manager.devices[selected]['id']
            try:
                subprocess.Popen(
                    f'start cmd /k adb -s {device_id} shell',
                    shell=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                error_msg = f'错误详情: {str(e)}'
                details = (
                    f'ADB Shell 启动失败:\n{error_msg}\n'
                    '常见问题排查:\n'
                    '1. 确认 adb.exe 在 PATH 环境变量中\n'
                    '2. 设备需要先成功连接\n'
                    '3. 允许程序通过防火墙\n'
                    '4. 尝试以管理员身份运行程序\n'
                )
                QMessageBox.critical(self, '错误', details)
        else:
            QMessageBox.warning(self, '警告', '请先选择设备。')

    def modify_alias(self):
        selected = self.list_widget.currentRow()
        if selected >= 0:
            device_id = self.device_manager.devices[selected]['id']
            current_alias = self.device_manager.devices[selected]['alias']

            dialog = InputDialog(self)
            dialog.setWindowTitle('修改设备别名')
            dialog.id_edit.setText(device_id)
            dialog.id_edit.setEnabled(False)
            dialog.alias_edit.setText(current_alias)

            if dialog.exec_() == QDialog.Accepted:
                new_alias = dialog.alias_edit.text().strip()
                self.device_manager.update_alias(device_id, new_alias)
                self.update_device_list()
        else:
            QMessageBox.warning(self, '警告', '请先选择要修改的设备。')

    def copy_device_id(self):
        selected = self.list_widget.currentRow()
        if selected >= 0:
            device_id = self.device_manager.devices[selected]['id']
            QApplication.clipboard().setText(device_id)
        else:
            QMessageBox.warning(self, '警告', '请先选择要复制的设备。')

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
