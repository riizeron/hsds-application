from forms import MainWindow
from PyQt5.QtWidgets import QApplication    
import sys

def application():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == '__main__':
    application()
