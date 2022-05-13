from _thread import start_new_thread
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.Qt import QStandardItem, QStandardItemModel

import sys
import os
import json
from session import *
from console import ConsoleWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setGeometry(400, 100, 500, 550)
        self.setWindowTitle("HSDS_APP")
        self.setWindowIcon(QtGui.QIcon('chrysanthemum_icon.png'))

        self.session = Session()
        
        centralWidget = QWidget(self)
        self.mainlayout = QFormLayout(centralWidget)
        centralWidget.setLayout(self.mainlayout)
        self.setCentralWidget(centralWidget)

        menubar = MenuBar(self)
        self.setMenuBar(menubar)

        statusBar = StatusBar(self)
        self.setStatusBar(statusBar)
        self.metaDataWidget = MetadataWidget(self)
        self.treeView = TreeView(centralWidget)
        self.mainlayout.addRow(self.treeView, self.metaDataWidget)

    def tryConnect(self, endpoint, username, password, key):

        if key and key.lower() == "none":
            key = None
        res, message = self.session.pingServer(endpoint, username, password, key)
        if res:
            self.session.refresh(endpoint, username, password, key)

            connectionInfo = f"Connected: {self.session.server_endpoint}"
            self.statusBar().refresh(status=connectionInfo)
            self.menuBar().connection_window.statusBar().refresh(status=connectionInfo)
            success = QMessageBox()
            success.setWindowTitle("SUCCESS")
            success.setText("Connection established!                           ")
            success.setIcon(QMessageBox.Information)
            success.setStandardButtons(QMessageBox.Ok)
            success.setInformativeText(message)
            success.setDetailedText(self.session.getServerInfo())
            success.exec_()
            self.menuBar().connection_window.close()
            start_new_thread(self.treeView.refresh, ())
        else:
            error = QMessageBox()
            error.setWindowTitle("ERROR")
            error.setText("Connection error!                                    ")
            error.setIcon(QMessageBox.Critical)
            error.setStandardButtons(QMessageBox.Ok)
            error.setInformativeText(message)
            error.exec_()

        return res

class StatusBar(QStatusBar):
    def __init__(self, parent):
        super(QStatusBar, self).__init__(parent)

        self.label_status = QLabel("No connection...")
        self.label_path = QLabel("")
        self.label_type = QLabel("")
        hor_lay = QHBoxLayout()
        self.setLayout(hor_lay)
        self.addWidget(self.label_status, 3)
        self.addWidget(self.label_type, 1)
        self.addWidget(self.label_path, 2)
        self.setStyleSheet("background-color: yellow")
    
    def refresh(self, status=None, path=None, type=None):
        if status is not None:    
            self.label_status.setText(status)
        if path is not None:
            self.label_path.setText(path)
        if type is not None:
            self.label_type.setText(type)
            
        self.setStyleSheet("background-color: #7fff00")


class MetadataWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.setLayout(QVBoxLayout())

        scrollWidget = QWidget()
        scrollArea = QScrollArea()

        scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scrollArea.setWidgetResizable(True)

        self.form_layout_label = QFormLayout(scrollWidget)

        scrollArea.setWidget(scrollWidget)

        self.layout().addWidget(scrollArea)

    def addData(self, data: list):
        for item in data:
            self.form_layout_label.addRow(QLabel(item[0]), QLabel(item[1]))

    def rmData(self):
        for i in reversed(range(self.form_layout_label.count())): 
            self.form_layout_label.itemAt(i).widget().deleteLater()
    
    def refresh(self, data: list):
        self.rmData()
        self.addData(data)

        
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

                self.parent().metaDataWidget.refresh(info_list)
                
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
            self.upload_btn.setText(self.fileName)
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
        self.connection_window = None
        menuFile = self.addMenu("&File")
        menuFile.addAction('Open', self.open_click)
        menuFile.addAction('Upload', self.upload_click)

        menuEnv = self.addMenu("&Env")
        menuEnv.addAction('Connect', self.connect)
        menuEnv.addAction('Restart', self.restart)
        

        menuInfo = self.addAction('Info', self.info)

        menuConsole = self.addAction('Console', self.console_click)

    def console_click(self):
        console = ConsoleWidget("Console")
        console.show()
        return
        
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

            self.mainWindow.metaDataWidget.refresh(info_list)

            os.system(f"hsls {file_path}")

    def getPath(self, item):
        self.mainWindow.statusBar().refresh(path=self.treeModel.itemFromIndex(item).path, type=self.treeModel.itemFromIndex(item).type)

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
        
        # with open("treeModel.json" , "w") as write:
        #     json.dump(self.treeModel, write)



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
        self.setCentralWidget(QWidget())

        verticalLayoutWidget = QWidget(self.centralWidget())
        verticalLayoutWidget.setGeometry(QtCore.QRect(10, 50, 470, 200))
        verticalLayout = QVBoxLayout(verticalLayoutWidget)
        verticalLayout.setContentsMargins(0, 0, 0, 0)

        self.label_endpoint = QLabel(f'Server endpoint [{parent.session.server_endpoint}]:')
        verticalLayout.addWidget(self.label_endpoint)

        self.lineEdit_endpoint = QLineEdit()
        if parent.session.server_endpoint is not None:
            self.lineEdit_endpoint.setText(parent.session.server_endpoint)
        verticalLayout.addWidget(self.lineEdit_endpoint)

        self.label_username = QLabel(f'Username [{parent.session.username}]:')
        verticalLayout.addWidget(self.label_username)

        self.lineEdit_username = QLineEdit()
        if parent.session.username is not None:
            self.lineEdit_username.setText(parent.session.username)
        verticalLayout.addWidget(self.lineEdit_username)

        self.label_password = QLabel(f'Password [{parent.session.password}]:')
        verticalLayout.addWidget(self.label_password)

        self.lineEdit_password = QLineEdit()
        if parent.session.password is not None:
            self.lineEdit_password.setText(parent.session.password)
        verticalLayout.addWidget(self.lineEdit_password)

        self.label_key = QLabel(f'API Key [{parent.session.api_key}]:')
        verticalLayout.addWidget(self.label_key)

        self.lineEdit_key = QLineEdit()
        self.lineEdit_key.setText(parent.session.api_key)
        verticalLayout.addWidget(self.lineEdit_key)

        horizontalLayoutWidget = QWidget(self.centralWidget())
        horizontalLayoutWidget.setGeometry(QtCore.QRect(170, 260, 160, 50))
        horizontalLayout = QHBoxLayout(horizontalLayoutWidget)
        horizontalLayout.setContentsMargins(0, 0, 0, 0)

        connectButton = QPushButton("&Connect")
        connectButton.clicked.connect(self.connect)
        horizontalLayout.addWidget(connectButton)

        cancelButton = QPushButton("&Cancel")
        cancelButton.clicked.connect(self.close)
        horizontalLayout.addWidget(cancelButton)

        label_title = QLabel("Input connection data", self.centralWidget())
        label_title.setGeometry(QtCore.QRect(160, 10, 180, 20))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        label_title.setFont(font)
        label_title.setAlignment(QtCore.Qt.AlignCenter)

        statusBar = StatusBar(self)
        self.setStatusBar(statusBar)
    
    def connect(self):
        self.updateUiData()
        self.parent.tryConnect(self.lineEdit_endpoint.text(), self.lineEdit_username.text(),
            self.lineEdit_password.text(), self.lineEdit_key.text())

    def updateUiData(self):
        self.label_endpoint.setText(f'Server endpoint [{self.parent.session.server_endpoint}]:')
        self.label_username.setText(f'Username [{self.parent.session.username}]:')
        self.label_password.setText(f'Password [{self.parent.session.password}]:')
        self.label_key.setText(f'API Key [{self.parent.session.api_key}]:')
