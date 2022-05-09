from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.Qt import QStandardItem, QStandardItemModel
from PyQt5.QtGui import QColor, QFont

import sys
import os
from session import *


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setGeometry(400, 100, 500, 550)
        self.setWindowTitle("HSDS_APP")


        self.session = Session()

        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)

        self.lay = QFormLayout(self.centralWidget)
        self.centralWidget.setLayout(self.lay)

        self.menubar = MenuBar(self)
        self.setMenuBar(self.menubar)

        model = QFileSystemModel()
        model.setRootPath(QtCore.QDir.currentPath())

        self.treeView = TreeView(self.centralWidget)
        self.lay.addWidget(self.treeView)

        self.label_status = QLabel("No connection...", self.statusBar())
        self.label_path = QLabel("", self.statusBar())
        self.label_type = QLabel("", self.statusBar())
        hor_lay = QHBoxLayout(self.statusBar())
        self.statusBar().setLayout(hor_lay)
        self.statusBar().addWidget(self.label_status, 3)
        self.statusBar().addWidget(self.label_type, 1)
        self.statusBar().addWidget(self.label_path, 2)
        self.statusBar().setStyleSheet("background-color: yellow")


class MenuBar(QMenuBar):
    def __init__(self, parent: MainWindow):
        super(QMenuBar, self).__init__(parent)
        self.setGeometry(QtCore.QRect(0, 0, 500, 20))

        self.parent = parent

        menuFile = self.addMenu("&File")
        menuFile.addAction('Open', self.open_click)

        menuEnv = self.addMenu("&Env")
        menuEnv.addAction('Connect', self.connect)
        menuEnv.addAction('Restart', self.restart)
        menuEnv.addSeparator()
        menuEnv.addAction('Disconnect', self.disconnect)

    def open_click(self):
        return

    def connect(self):
        connection_window = ConnectionWindow(self.parent)
        connection_window.show()

    def restart(self):
        return

    def disconnect(self):
        return


class TreeView(QTreeView):
    def __init__(self, parent: QWidget):
        super(QTreeView, self).__init__(parent)

        self.mainWindow = self.parent().parent()
        self.setHeaderHidden(False)
        self.setGeometry(0, 0, 350, 500)

        self.treeModel = QStandardItemModel(self)

        self.setModel(self.treeModel)
        self.expandAll()
        self.clicked.connect(self.getPath)
        # self.doubleClicked.connect()

    def getPath(self, item):
        self.mainWindow.label_path.setText(self.treeModel.itemFromIndex(item).path)
        self.mainWindow.label_type.setText(self.treeModel.itemFromIndex(item).type)

    def refresh(self):
        self.treeModel.clear()
        self.fillTree()

    def fillTree(self, path=None, parent=None):
        res, domain = self.mainWindow.session.getDomain(path)
        print(domain)
        if res:
            is_folder = domain.domain.endswith('/')
            if is_folder:
                name = domain.domain.split('/')[-2]
                type = "folder"
                path = domain.domain
            else:
                name = domain.filename.split('/')[-1]
                type = "domain"
                path = domain.filename

            subdomains = domain._getSubdomains()
            domain.close()

            newItem = TreeViewItem(name)
            newItem.setPath(path)
            newItem.setType(type)
            
            if parent is None:
                self.treeModel.appendRow(newItem)
            else:
                parent.appendRow(newItem)
            for d in subdomains:
                newPath = str(path) + str(d)
                if is_folder:
                    self.fillTree(newPath, newItem)


class TreeViewItem(QStandardItem):
    def ___init__(self, text):
        super(TreeViewItem, self).__init__(text)

        self.path = None
        self.type = None
        self.setEditable(False)
    
    def setType(self, type):
        self.type = type

    def setPath(self, path):
        self.path = path



class ConnectionWindow(QMainWindow):
    def __init__(self, parent: MainWindow):
        super(QMainWindow, self).__init__(parent)

        self.parent = parent

        self.setGeometry(400, 100, 500, 350)
        self.setWindowTitle("CONNECTION")
        self.setCentralWidget(QWidget(self))

        verticalLayoutWidget = QWidget(self.centralWidget())
        verticalLayoutWidget.setGeometry(QtCore.QRect(10, 50, 470, 200))
        verticalLayout = QVBoxLayout(verticalLayoutWidget)
        verticalLayout.setContentsMargins(0, 0, 0, 0)

        self.label_endpoint = QLabel(f'Server endpoint [{parent.session.server_endpoint}]:', verticalLayoutWidget)
        verticalLayout.addWidget(self.label_endpoint)

        self.lineEdit_endpoint = QLineEdit(verticalLayoutWidget)
        if parent.session.server_endpoint is not None:
            self.lineEdit_endpoint.setText(parent.session.server_endpoint)
        verticalLayout.addWidget(self.lineEdit_endpoint)

        self.label_username = QLabel(f'Username [{parent.session.username}]:', verticalLayoutWidget)
        verticalLayout.addWidget(self.label_username)

        self.lineEdit_username = QLineEdit(verticalLayoutWidget)
        if parent.session.username is not None:
            self.lineEdit_username.setText(parent.session.username)
        verticalLayout.addWidget(self.lineEdit_username)

        self.label_password = QLabel(f'Password [{parent.session.password}]:', verticalLayoutWidget)
        verticalLayout.addWidget(self.label_password)

        self.lineEdit_password = QLineEdit(verticalLayoutWidget)
        if parent.session.password is not None:
            self.lineEdit_password.setText(parent.session.password)
        verticalLayout.addWidget(self.lineEdit_password)

        self.label_key = QLabel(f'API Key [{parent.session.api_key}]:', verticalLayoutWidget)
        verticalLayout.addWidget(self.label_key)

        self.lineEdit_key = QLineEdit(verticalLayoutWidget)
        verticalLayout.addWidget(self.lineEdit_key)

        horizontalLayoutWidget = QWidget(self.centralWidget())
        horizontalLayoutWidget.setGeometry(QtCore.QRect(170, 260, 160, 50))
        horizontalLayout = QHBoxLayout(horizontalLayoutWidget)
        horizontalLayout.setContentsMargins(0, 0, 0, 0)

        connectButton = QPushButton("&Connect", horizontalLayoutWidget)
        connectButton.clicked.connect(self.tryConnect)
        horizontalLayout.addWidget(connectButton)

        cancelButton = QPushButton("&Cancel", horizontalLayoutWidget)
        cancelButton.clicked.connect(self.close)
        horizontalLayout.addWidget(cancelButton)

        label_title = QLabel("Input connection data", self.centralWidget())
        label_title.setGeometry(QtCore.QRect(160, 10, 160, 20))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        label_title.setFont(font)
        label_title.setAlignment(QtCore.Qt.AlignCenter)

        self.label_status = QLabel("No connection...", self.statusBar())
        self.statusBar().addWidget(self.label_status)
        self.statusBar().setStyleSheet("background-color: yellow")

    def tryConnect(self):
        self.parent.session.server_endpoint = self.lineEdit_endpoint.text() if len(
            self.lineEdit_endpoint.text()) > 0 else None
        self.parent.session.username = self.lineEdit_username.text() if len(self.lineEdit_username.text()) > 0 else None
        self.parent.session.password = self.lineEdit_password.text() if len(self.lineEdit_password.text()) > 0 else None
        self.parent.session.api_key = self.lineEdit_key.text() if self.lineEdit_key is not None else ""

        self.label_endpoint.setText(f'Server endpoint [{self.parent.session.server_endpoint}]:')
        self.label_username.setText(f'Username [{self.parent.session.username}]:')
        self.label_password.setText(f'Password [{self.parent.session.password}]:')
        self.label_key.setText(f'API Key [{self.parent.session.api_key}]:')

        res, message = self.parent.session.pingServer()
        if res:
            self.parent.label_status.setText(f"Connected: {self.parent.session.server_endpoint}")
            success = QMessageBox()
            success.setWindowTitle("SUCCESS")
            success.setText("Connection established!                           ")
            success.setIcon(QMessageBox.Information)
            success.setStandardButtons(QMessageBox.Ok)
            success.setInformativeText(message)
            success.setDetailedText(self.parent.session.getServerInfo())
            success.exec_()
            self.close()
            self.parent.treeView.refresh()
        else:
            error = QMessageBox()
            error.setWindowTitle("ERROR")
            error.setText("Connection error!                                    ")
            error.setIcon(QMessageBox.Critical)
            error.setStandardButtons(QMessageBox.Ok)
            error.setInformativeText(message)
            error.exec_()


def application():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == '__main__':
    application()
