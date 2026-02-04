# -*- coding: utf-8 -*-
import sys
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QMenu, QAction
from main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont('Microsoft YaHei', 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
