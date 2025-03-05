import sys
from PyQt5.QtWidgets import QApplication, QMenu, QAction
from main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    # menu = QMenu()
    
    # # 将 self 改为 window
    # connect_action = QAction('连接设备', window)
    # connect_action.triggered.connect(window.connect_device)
    # menu.addAction(connect_action)

    # delete_action = QAction('删除设备', window)
    # delete_action.triggered.connect(window.delete_device)
    # menu.addAction(delete_action)

    # scrcpy_action = QAction('启动scrcpy', window)
    # scrcpy_action.triggered.connect(window.start_scrcpy)
    # menu.addAction(scrcpy_action)
    
    window.show()
    sys.exit(app.exec_())