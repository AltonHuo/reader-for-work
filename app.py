from abc import abstractmethod

from PySide6 import QtGui
from PySide6.QtWidgets import QApplication, QWidget, QTabWidget, QVBoxLayout, QFileDialog, QMessageBox, QPushButton
from filetab import FileTab
from settingdata import settingData
from settingtab import SettingsTab
import sys
import os
import configparser
from readwindow import ReadWindow, get_most_recent_file


class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        try:
            settingData.readData()
            print(settingData)
        except Exception as e:
            print(e)

        # 创建选项卡部件
        self.tabWidget = QTabWidget()

        # 创建文件选项卡
        self.fileTab = FileTab()
        # 添加文件选项卡到 QTabWidget
        self.tabWidget.addTab(self.fileTab, "文件")

        # 创建设置选项卡
        self.settingTab = SettingsTab()
        # 添加设置选项卡到 QTabWidget
        self.tabWidget.addTab(self.settingTab, "设置")

        # 创建主布局
        layout = QVBoxLayout(self)
        
        # 添加"打开上次阅读的文件"按钮
        self.lastFileButton = QPushButton("打开上次阅读的文件")
        self.lastFileButton.clicked.connect(self.openLastFile)
        
        # 检查是否有上次阅读的文件
        last_file = self.getLastFile()
        if last_file and os.path.exists(last_file):
            self.lastFileButton.setText(f"打开上次阅读的文件: {os.path.basename(last_file)}")
            self.lastFileButton.setToolTip(last_file)
        else:
            self.lastFileButton.setEnabled(False)
            self.lastFileButton.setText("没有找到上次阅读的文件")
        
        # 添加"打开历史记录"按钮
        self.historyButton = QPushButton("查看阅读历史")
        self.historyButton.clicked.connect(self.openHistoryFile)
        
        # 检查是否有历史记录
        if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")):
            self.historyButton.setEnabled(False)
        
        # 添加按钮到布局
        layout.addWidget(self.lastFileButton)
        layout.addWidget(self.historyButton)
        layout.addWidget(self.tabWidget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

    def initUI(self):
        self.setWindowTitle('阅读器')
        # 设置总体程序大小默认300 * 200
        self.setGeometry(0, 0, 400, 300)
        self.center()

    def center(self):
        # 获取屏幕的中心点
        screen = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        self.move(int((screen.width() - size.width()) / 2), int((screen.height() - size.height()) / 2))

    def closeEvent(self, event):
        settingData.writeData()
        event.accept()
    
    def getLastFile(self):
        """获取上次阅读的文件路径"""
        # 首先尝试从settingData获取
        if settingData.filePath and os.path.exists(settingData.filePath):
            return settingData.filePath
        
        # 然后尝试从settings.ini直接读取
        try:
            config = configparser.ConfigParser()
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.ini")
            
            if os.path.exists(settings_path):
                config.read(settings_path, encoding='utf-8')
                if 'file' in config and 'filepath' in config['file']:
                    file_path = config['file']['filepath']
                    if os.path.exists(file_path):
                        return file_path
        except Exception:
            pass
        
        # 最后尝试从历史记录获取
        try:
            return get_most_recent_file()
        except Exception:
            pass
        
        return None
    
    def openLastFile(self):
        """打开上次阅读的文件"""
        file_path = self.lastFileButton.toolTip()
        if file_path and os.path.exists(file_path):
            self.openReadWindow(file_path)
        else:
            QMessageBox.warning(self, "错误", "无法打开上次阅读的文件，文件可能已被移动或删除。")
    
    def openHistoryFile(self):
        """打开历史记录窗口"""
        # 创建一个临时的ReadWindow来显示历史记录
        try:
            temp_window = ReadWindow(self.getLastFile())
            temp_window.displayHistory()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开历史记录: {str(e)}")
    
    def openReadWindow(self, file_path):
        """打开阅读窗口"""
        try:
            self.read_window = ReadWindow(file_path)
            self.read_window.show()
            # 隐藏选择窗口
            self.hide()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件时出错: {str(e)}")


def main():
    app = QApplication(sys.argv)
    
    # 创建并显示主窗口
    window = MyWindow()
    window.show()
    
    # 运行应用程序
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
