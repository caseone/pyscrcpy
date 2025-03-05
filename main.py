import sys
from PyQt5.QtWidgets import QApplication, QMenu, QAction
from main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())