from curses.textpad import Textbox
from pathlib import Path
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

        self.form_layout = QFormLayout(self.centralWidget)
        self.centralWidget.setLayout(self.form_layout)

        self.menubar = MenuBar(self)
        self.setMenuBar(self.menubar)

        self.widg = QWidget()
        self.scrollWidget = QWidget()
        self.scrollArea = QScrollArea()
        self.form_layout_label = QFormLayout(self.scrollWidget)

        self.scrollArea.setWidget(self.scrollWidget)
        self.widg.setLayout(QVBoxLayout())
        self.widg.layout().addWidget(self.scrollArea)
        
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setWidgetResizable(True)

        self.treeView = TreeView(self.centralWidget)
        self.form_layout.addRow(self.treeView, self.widg)

        self.label_status = QLabel("No connection...", self.statusBar())
        self.label_path = QLabel("", self.statusBar())
        self.label_type = QLabel("", self.statusBar())
        hor_lay = QHBoxLayout(self.statusBar())
        self.statusBar().setLayout(hor_lay)
        self.statusBar().addWidget(self.label_status, 3)
        self.statusBar().addWidget(self.label_type, 1)
        self.statusBar().addWidget(self.label_path, 2)
        self.statusBar().setStyleSheet("background-color: yellow")

    def tryConnect(self):
        res, message = self.session.pingServer()
        if res:
            self.label_status.setText(f"Connected: {self.session.server_endpoint}")
            success = QMessageBox()
            success.setWindowTitle("SUCCESS")
            success.setText("Connection established!                           ")
            success.setIcon(QMessageBox.Information)
            success.setStandardButtons(QMessageBox.Ok)
            success.setInformativeText(message)
            success.setDetailedText(self.session.getServerInfo())
            success.exec_()
            self.menubar.connection_window.close()
            self.treeView.refresh()
        else:
            error = QMessageBox()
            error.setWindowTitle("ERROR")
            error.setText("Connection error!                                    ")
            error.setIcon(QMessageBox.Critical)
            error.setStandardButtons(QMessageBox.Ok)
            error.setInformativeText(message)
            error.exec_()

        return res

class OpenWindow(QMainWindow):
    def __init__(self, parent):
        super(QMainWindow, self).__init__(parent)
        self.setGeometry(200, 200, 300, 200)
        self.setWindowTitle('OPEN FILE')

        widget = QWidget()
        self.vbox = QVBoxLayout()
        widget.setLayout(self.vbox)
        self.setCentralWidget(widget)

        label = QLabel('Type file PATH:')
        self.textBox = QLineEdit()
        self.submit_btn = QPushButton("&Submit")
        self.submit_btn.clicked.connect(self.submit)
        self.cancel_btn = QPushButton("&Cancel")
        self.cancel_btn.clicked.connect(self.close)

        self.vbox.addWidget(label)
        self.vbox.addWidget(self.textBox)
        self.vbox.addWidget(self.submit_btn)
        self.vbox.addWidget(self.cancel_btn)

    def submit(self):
        path = self.textBox.text()
        if path.endswith('/'):
            error = QMessageBox()
            error.setWindowTitle("ERROR")
            error.setText("Incorrect file format")
            error.setInformativeText("Please, try without '/'")
            error.setIcon(QMessageBox.Warning)
            error.setStandardButtons(QMessageBox.Ok)
            error.exec_()
        else:
            try:
                info_list = self.parent().session.dumpFile(path)
                for i in reversed(range(self.parent().form_layout_label.count())): 
                    self.parent().form_layout_label.itemAt(i).widget().deleteLater()
                for item in info_list:
                    self.parent().form_layout_label.addRow(QLabel(item[0]), QLabel(item[1]))
                os.system(f"hsls {path}")
            except Exception as e:
                error = QMessageBox()
                error.setWindowTitle("ERROR")
                error.setText("File Not Found")
                error.setInformativeText("Please, check your path or connect to HSDS if you forgot  ")
                error.setDetailedText(str(e))
                error.setIcon(QMessageBox.Critical)
                error.setStandardButtons(QMessageBox.Ok)
                error.exec_()

class UploadWindow(QMainWindow):
    def __init__(self, parent):
        super(QMainWindow, self).__init__(parent)
        self.setGeometry(200, 200, 300, 200)
        self.setWindowTitle('UPLOAD FILE')

        widget = QWidget()
        self.vbox = QVBoxLayout()
        widget.setLayout(self.vbox)
        self.setCentralWidget(widget)

        label1 = QLabel('Choose youe file')
        self.upload_btn = QPushButton("&FILE")
        self.upload_btn.clicked.connect(self.upload)

        label2 = QLabel('Type destination PATH:')
        self.textBox = QLineEdit()
        self.submit_btn = QPushButton("&Submit")
        self.submit_btn.clicked.connect(self.submit)
        self.cancel_btn = QPushButton("&Cancel")
        self.cancel_btn.clicked.connect(self.close)

        self.vbox.addWidget(label1)
        self.vbox.addWidget(self.upload_btn)
        self.vbox.addWidget(label2)
        self.vbox.addWidget(self.textBox)
        self.vbox.addWidget(self.submit_btn)
        self.vbox.addWidget(self.cancel_btn)

        self.fileName = None

    def upload(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
        if self.fileName:
            print(self.fileName)

    def submit(self):
        try:
            os.system(f"hsload -v -u {self.parent().session.username} -p {self.parent().session.password} "+
            f"-e {self.parent().session.server_endpoint} {self.fileName} {self.textBox.text()}")
        except Exception as e:
            print(str(e))
    

class MenuBar(QMenuBar):
    def __init__(self, parent: MainWindow):
        super(QMenuBar, self).__init__(parent)
        self.setGeometry(QtCore.QRect(0, 0, 500, 20))

        self.parent = parent

        menuFile = self.addMenu("&File")
        menuFile.addAction('Open', self.open_click)
        menuFile.addAction('Upload', self.upload_click)

        menuEnv = self.addMenu("&Env")
        menuEnv.addAction('Connect', self.connect)
        menuEnv.addAction('Restart', self.restart)
        menuEnv.addSeparator()
        menuEnv.addAction('Disconnect', self.disconnect)

        menuInfo = self.addAction('Info', self.info)

    def open_click(self):
        self.open_window = OpenWindow(self.parent)
        self.open_window.show()

    def upload_click(self):
        self.upload_window = UploadWindow(self.parent)
        self.upload_window.show()
    
    def info(self):
        info = QMessageBox()
        info.setWindowTitle("INFO")
        info.setText("Server information")
        info.setIcon(QMessageBox.Information)
        info.setStandardButtons(QMessageBox.Ok)
        info.setInformativeText(self.parent.session.getServerInfo())
        info.exec_()

    def connect(self):
        self.connection_window = ConnectionWindow(self.parent)
        self.connection_window.show()

    def restart(self):
        self.parent.tryConnect()

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
        self.doubleClicked.connect(self.fileDump)

    def fileDump(self, item):
        type = self.treeModel.itemFromIndex(item).type
        if type == 'domain':
            file_path = self.treeModel.itemFromIndex(item).path
            info_list = self.mainWindow.session.dumpFile(file_path)

            for i in reversed(range(self.mainWindow.form_layout_label.count())): 
                self.mainWindow.form_layout_label.itemAt(i).widget().deleteLater()

            for item in info_list:
                self.mainWindow.form_layout_label.addRow(QLabel(item[0]), QLabel(item[1]))
            os.system(f"hsls {file_path}")

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
            is_folder = str(domain).endswith('/')
            if is_folder:
                name = domain.domain.split('/')[-2]
                type = "folder"
                path = domain.domain
            else:
                name = domain.filename.split('/')[-1]
                type = "domain"
                path = domain.filename

            newItem = TreeViewItem(name)
            newItem.setPath(path)
            newItem.setType(type)
            
            if parent is None:
                self.treeModel.appendRow(newItem)
            else:
                parent.appendRow(newItem)
            for d in domain:
                newPath = str(path) + str(d)
                if is_folder:
                    self.fillTree(newPath, newItem)
            domain.close()


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
        connectButton.clicked.connect(self.connect)
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
    
    def connect(self):
        self.updateData()
        self.parent.tryConnect()

    def updateData(self):
        self.parent.session.server_endpoint = self.lineEdit_endpoint.text() if len(
            self.lineEdit_endpoint.text()) > 0 else None
        self.parent.session.username = self.lineEdit_username.text() if len(self.lineEdit_username.text()) > 0 else None
        self.parent.session.password = self.lineEdit_password.text() if len(self.lineEdit_password.text()) > 0 else None
        self.parent.session.api_key = self.lineEdit_key.text() if self.lineEdit_key is not None else ""

        self.label_endpoint.setText(f'Server endpoint [{self.parent.session.server_endpoint}]:')
        self.label_username.setText(f'Username [{self.parent.session.username}]:')
        self.label_password.setText(f'Password [{self.parent.session.password}]:')
        self.label_key.setText(f'API Key [{self.parent.session.api_key}]:')


def application():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == '__main__':
    application()
