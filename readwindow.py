import re
import time
import os
import json
from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLineEdit, QPushButton, QHBoxLayout
from PySide6.QtWidgets import QLabel  # 移除进度对话框相关组件
from PySide6.QtCore import Qt, QPoint, QSize  # 移除不需要的导入
from PySide6.QtGui import QMouseEvent, QGuiApplication, QPainter, QPen, QColor, QFontMetrics, \
    QKeySequence, QShortcut, QAction, QIcon, QPixmap
from settingdata import settingData


# 支持的编码格式
def readText(fileName):
    # 读取文本
    if settingData.filePath != fileName:
        settingData.currentPage = 0
        settingData.lastPage = 0
        settingData.pages = [0] * settingData.pageSize
    settingData.filePath = fileName

    encodings = ['utf-8', 'Windows-1252', 'ANSI', 'gbk', 'ISO-8859-1', 'big5']  # 增加其他编码格式
    # 尝试每种编码格式
    for encoding in encodings:
        try:
            with open(fileName, 'r', encoding=encoding) as file:
                text = file.read()
                return text
        except (UnicodeDecodeError, LookupError):
            pass
        except FileNotFoundError:
            # 如果文件不存在，尝试从历史记录中找到最近的文件
            try:
                recent_file = get_most_recent_file()
                if recent_file and os.path.exists(recent_file):
                    settingData.filePath = recent_file
                    return readText(recent_file)
                else:
                    raise IOError(f"文件 {fileName} 不存在，且没有可用的历史记录")
            except Exception as e:
                raise IOError(f"文件 {fileName} 不存在: {str(e)}")

    # 如果所有编码都失败，抛出异常
    raise IOError(f"Could not decode the file {fileName} with any of the encodings: {encodings}")


def get_most_recent_file():
    """获取最近打开的文件"""
    history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")

    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            # 遍历历史记录，找到第一个存在的文件
            for item in history:
                file_path = item['path']
                if os.path.exists(file_path):
                    return file_path
        except Exception:
            pass

    return None


def open_last_file():
    """打开上次阅读的文件"""
    # 首先尝试从settings.ini读取
    last_file = settingData.filePath

    # 确保设置数据已加载
    if not last_file or last_file == "":
        settingData.readData()
        last_file = settingData.filePath

    print(f"尝试打开上次文件: {last_file}")

    # 检查文件是否存在
    if last_file and os.path.exists(last_file):
        print(f"文件存在，将打开: {last_file}")
        return last_file
    else:
        print(f"文件不存在: {last_file}")

    # 如果settings.ini中的文件不存在，尝试从历史记录中获取
    recent_file = get_most_recent_file()
    if recent_file:
        print(f"从历史记录中找到文件: {recent_file}")
    else:
        print("历史记录中没有可用文件")

    return recent_file


class ReadWindow(QWidget):
    def __init__(self, fileName=None):
        super().__init__()

        # 如果没有提供文件名，尝试打开上次阅读的文件
        if fileName is None or not os.path.exists(fileName):
            fileName = open_last_file()

            # 如果仍然没有可用的文件，显示错误消息并退出
            if fileName is None:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "错误", "没有找到可以打开的文件。请先选择一个文件。")
                import sys
                sys.exit(1)

        # 添加文件到历史记录
        self.addToHistory(fileName)

        try:
            self.textContent = readText(fileName)
            self.text, _ = self.rollPage(settingData.currentPage)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "错误", f"无法读取文件: {str(e)}")
            import sys
            sys.exit(1)

        self.initUI()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 添加一个标志来跟踪是否需要完全重绘
        self.needFullRepaint = True

        # 添加大小调整相关变量
        self.resizing = False
        self.resizeDirection = None
        self.resizeMargin = 10  # 边缘调整大小的区域宽度

        self.selectChapter = QAction('选择章节')
        self.closeSelf = QAction('关闭')
        self.history = QAction('历史记录')
        self.setAction()
        self.scrollableMenu = None
        self.historyMenu = None

        self.qPen = QPen(settingData.qColor)

        # 初始化鼠标按下的位置
        self.mousePosition = QPoint()
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)

        # 添加快捷键
        self.next = QShortcut(QKeySequence(settingData.nextShortCut), self)
        self.last = QShortcut(QKeySequence(settingData.lastShortCut), self)
        self.next.activated.connect(lambda: self.rollPageActive(settingData.currentPage + 1))
        self.last.activated.connect(lambda: self.rollPageActive(settingData.currentPage - 1))

    def paintEvent(self, event):
        # 创建一个全新的QPixmap作为绘制表面
        pixmap = QPixmap(self.size())
        # 使pixmap完全透明
        pixmap.fill(Qt.GlobalColor.transparent)

        # 在pixmap上创建一个新的painter
        temp_painter = QPainter(pixmap)
        temp_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        temp_painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # 设置字体和画笔
        temp_painter.setFont(settingData.qFont)
        temp_painter.setPen(self.qPen)

        # 绘制一个几乎透明的背景，以便接收鼠标事件
        temp_painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        # 绘制文本
        textLines = self.text.split('\n')
        metrics = QFontMetrics(settingData.qFont)
        yPosition = metrics.ascent()
        for line in textLines:
            temp_painter.drawText(QPoint(0, yPosition), line)
            yPosition += metrics.height() + settingData.lineSpacing

        # 完成pixmap上的绘制
        temp_painter.end()

        # 现在将pixmap绘制到窗口上
        window_painter = QPainter(self)

        # 如果需要完全重绘，先清除整个窗口
        if self.needFullRepaint:
            window_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            window_painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
            window_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            self.needFullRepaint = False

        window_painter.drawPixmap(0, 0, pixmap)

    def initUI(self):
        # 计算文本高度和宽度
        fontMetrics = QFontMetrics(settingData.qFont)
        textWidth = fontMetrics.horizontalAdvance('中') * settingData.lineSize
        textHeight = (fontMetrics.height() + settingData.lineSpacing) * settingData.textLine - settingData.lineSpacing
        # 获取主屏幕
        screen = QGuiApplication.primaryScreen()
        # 获取屏幕的尺寸
        size = screen.size()
        screenWidth = size.width()
        screenHeight = size.height()

        x = screenWidth - 500
        y = screenHeight - 200
        self.setGeometry(x, y, textWidth, textHeight)

    # 根据mark来移动标记的指针，正向
    def subText(self, mark):
        count = 0
        line = 0
        string = ""
        for i in range(mark, len(self.textContent)):
            char = self.textContent[i]
            # 将多个换行符作为一个换行符进行拼接
            if char == '\n':
                try:
                    if self.textContent[i + 1] != '\n':
                        # 如果下一个字符不是换行符，拼接
                        string += char
                        count = 0
                        line += 1
                # 可能到最后一个字符
                except IndexError:
                    string += char
                    break
            else:
                string += char
                count += 1
                if count >= settingData.lineSize:
                    string += '\n'
                    count = 0
                    line += 1
            mark += 1
            if line >= settingData.textLine:
                break
        return string, mark

    # 翻页功能，查找并处理文本
    def rollPage(self, page):
        if page < 0:
            return None, None
        pageOffset = page - settingData.lastPage
        if pageOffset >= 0:
            text, nextMark = self.subText(settingData.pages[page % settingData.pageSize])
            if len(text) == 0:
                return None, None
            settingData.currentPage = page
            settingData.pages[(page + 1) % settingData.pageSize] = nextMark
            settingData.lastPage += 1
            return text, nextMark
        else:
            if -pageOffset < settingData.pageSize:
                settingData.currentPage = page
                text, nextMark = self.subText(settingData.pages[page % settingData.pageSize])
                return text, nextMark
            else:
                return None, None

    def nativeEvent(self, eventType, message):
        # 处理Windows系统的WM_NCHITTEST消息，以允许拖拽
        if eventType == "windows_generic_msg":
            msg = message
            if msg.window() == self.winId() and msg.message() == 0x84:  # WM_NCHITTEST
                x = msg.lParam() & 0xFFFF
                y = msg.lParam() >> 16
                if self.rect().contains(QPoint(x, y)):
                    # 返回HTCAPTION，让系统知道点击的是标题栏区域
                    return True, 1  # HTCAPTION
        return super().nativeEvent(eventType, message)

    def setAction(self):
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.addAction(self.selectChapter)
        self.addAction(self.history)
        self.addAction(self.closeSelf)
        self.selectChapter.triggered.connect(self.displayChapter)
        self.history.triggered.connect(self.displayHistory)
        self.closeSelf.triggered.connect(self.close)

    def displayChapter(self):
        self.scrollableMenu = ScrollableMenu(self)
        self.scrollableMenu.show()

    def displayHistory(self):
        """显示历史记录窗口"""
        self.historyMenu = HistoryMenu(self)
        self.historyMenu.show()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # 检查是否在窗口边缘
        x, y = event.pos().x(), event.pos().y()
        width, height = self.width(), self.height()

        # 确定调整方向
        if event.button() == Qt.MouseButton.LeftButton:
            # 左边缘
            if x <= self.resizeMargin:
                self.resizeDirection = "left"
                self.resizing = True
            # 右边缘
            elif x >= width - self.resizeMargin:
                self.resizeDirection = "right"
                self.resizing = True
            # 上边缘
            elif y <= self.resizeMargin:
                self.resizeDirection = "top"
                self.resizing = True
            # 下边缘
            elif y >= height - self.resizeMargin:
                self.resizeDirection = "bottom"
                self.resizing = True
            # 如果不是在边缘，则为拖动窗口
            else:
                self.resizing = False
                self.mousePosition = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        # 如果正在调整大小
        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            x, y = event.pos().x(), event.pos().y()
            geometry = self.geometry()

            if self.resizeDirection == "left":
                width = geometry.width() - x
                self.setGeometry(geometry.x() + x, geometry.y(), width, geometry.height())
            elif self.resizeDirection == "right":
                width = x
                self.setGeometry(geometry.x(), geometry.y(), width, geometry.height())
            elif self.resizeDirection == "top":
                height = geometry.height() - y
                self.setGeometry(geometry.x(), geometry.y() + y, geometry.width(), height)
            elif self.resizeDirection == "bottom":
                height = y
                self.setGeometry(geometry.x(), geometry.y(), geometry.width(), height)

            # 更新文本布局以适应新的窗口大小
            self.updateTextLayout()
        # 如果是拖动窗口
        elif event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.pos() - self.mousePosition
            self.move(self.x() + delta.x(), self.y() + delta.y())
        # 更新鼠标指针形状
        else:
            self.updateCursorShape(event.pos())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.resizing = False
        self.mousePosition = QPoint()
        # 重置鼠标指针
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def updateCursorShape(self, pos):
        x, y = pos.x(), pos.y()
        width, height = self.width(), self.height()

        # 左边缘或右边缘
        if x <= self.resizeMargin or x >= width - self.resizeMargin:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        # 上边缘或下边缘
        elif y <= self.resizeMargin or y >= height - self.resizeMargin:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        # 不在边缘
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def rollPageActive(self, page):
        text, _ = self.rollPage(page)
        if text:
            self.text = text
            self.needFullRepaint = True

            # 强制完全重绘
            self.hide()
            self.show()

    def enterEvent(self, event: QMouseEvent) -> None:
        self.qPen = QPen(settingData.qColor)
        self.update()

    def leaveEvent(self, event: QMouseEvent) -> None:
        self.qPen = QPen(settingData.outColor)
        self.update()

    def closeEvent(self, event):
        settingData.writeData()
        event.accept()

    def getChapter(self):
        chapter = {}
        page = 0
        mark = 0
        temp, mark = self.subText(mark)
        pattern = re.compile(r'(第)([\u4e00-\u9fa5a-zA-Z0-9]{1,7})[章|节].{0,20}(\n|$)')

        while len(temp) > 1:
            lines = temp.splitlines()
            for i in range(len(lines)):
                line = lines[i].strip()
                if re.match(pattern, line):
                    chapter[line] = page
            page += 1
            temp, mark = self.subText(mark)
        return chapter

    def jumpToChapter(self, item, chapter):
        text = ''
        page = chapter[item.text()]
        settingData.currentPage = page
        settingData.lastPage = page
        mark = 0
        for i in range(0, page + 1):
            settingData.pages[i % settingData.pageSize] = mark
            text, mark = self.subText(mark)
        settingData.pages[(page + 1) % settingData.pageSize] = mark
        self.text = text
        self.update()

    def resizeEvent(self, event):
        """当窗口大小改变时调用此方法"""
        super().resizeEvent(event)
        # 重新计算文本布局
        self.updateTextLayout()
        # 标记需要完全重绘
        self.needFullRepaint = True
        # 更新显示
        self.update()

    def updateTextLayout(self):
        """更新文本布局以适应当前窗口大小"""
        # 获取当前窗口大小
        width = self.width()
        height = self.height()

        # 计算每行可以容纳的字符数
        fontMetrics = QFontMetrics(settingData.qFont)
        charWidth = fontMetrics.horizontalAdvance('中')  # 使用中文字符宽度作为参考
        lineHeight = fontMetrics.height() + settingData.lineSpacing

        # 计算新的行大小和行数
        newLineSize = max(1, int(width / charWidth))
        newTextLine = max(1, int(height / lineHeight))

        # 如果行大小或行数发生变化，更新设置并重新加载文本
        if newLineSize != settingData.lineSize or newTextLine != settingData.textLine:
            settingData.lineSize = newLineSize
            settingData.textLine = newTextLine

            # 重新加载当前页面的文本
            self.text, _ = self.rollPage(settingData.currentPage)

    def addToHistory(self, filePath):
        """添加文件到历史记录"""
        # 历史记录文件路径
        history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")

        # 读取现有历史记录
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # 如果文件损坏，创建新的历史记录
                history = []

        # 检查文件是否已在历史记录中
        for item in history:
            if item['path'] == filePath:
                # 如果已存在，更新访问时间并移到列表前面
                history.remove(item)
                break

        # 添加新记录到列表前面
        history.insert(0, {
            'path': filePath,
            'name': os.path.basename(filePath),
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        # 限制历史记录数量为20条
        history = history[:20]

        # 保存历史记录
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def openHistoryFile(self, filePath):
        """打开历史记录中的文件"""
        if os.path.exists(filePath):
            # 关闭当前窗口
            self.close()

            # 创建新窗口打开选定的文件
            from main import createReadWindow  # 导入创建窗口的函数
            createReadWindow(filePath)
        else:
            # 文件不存在，显示错误消息
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "文件不存在", f"文件 {filePath} 不存在或已被移动。")

            # 从历史记录中移除不存在的文件
            self.removeFromHistory(filePath)

    def removeFromHistory(self, filePath):
        """从历史记录中移除文件"""
        history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")

        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)

                # 移除指定文件
                history = [item for item in history if item['path'] != filePath]

                # 保存更新后的历史记录
                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"更新历史记录失败: {e}")


class ScrollableMenu(QWidget):
    def __init__(self, readWindow):
        super().__init__()
        chapter = readWindow.getChapter()
        self.setWindowTitle('选择章节')
        layout = QVBoxLayout(self)

        listWidget = QListWidget()
        for key in chapter.keys():
            listWidget.addItem(QListWidgetItem(key))
        listWidget.itemDoubleClicked.connect(lambda item: readWindow.jumpToChapter(item, chapter))

        layout.addWidget(listWidget)


class HistoryMenu(QWidget):
    def __init__(self, readWindow):
        super().__init__()
        self.readWindow = readWindow
        self.setWindowTitle('历史记录')

        # 创建主布局
        layout = QVBoxLayout(self)

        # 创建标签
        label = QLabel("最近打开的文件:")
        layout.addWidget(label)

        # 创建列表控件
        self.listWidget = QListWidget()
        self.listWidget.setAlternatingRowColors(True)
        layout.addWidget(self.listWidget)

        # 加载历史记录
        self.loadHistory()

        # 创建按钮区域
        buttonLayout = QHBoxLayout()

        # 清除按钮
        self.clearButton = QPushButton("清除历史")
        self.clearButton.clicked.connect(self.clearHistory)
        buttonLayout.addWidget(self.clearButton)

        # 关闭按钮
        self.closeButton = QPushButton("关闭")
        self.closeButton.clicked.connect(self.close)
        buttonLayout.addWidget(self.closeButton)

        # 添加按钮区域到主布局
        layout.addLayout(buttonLayout)

        # 设置窗口大小
        self.resize(500, 400)

        # 连接双击事件
        self.listWidget.itemDoubleClicked.connect(self.openHistoryItem)

    def loadHistory(self):
        """加载历史记录"""
        history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")

        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)

                # 清空列表
                self.listWidget.clear()

                # 添加历史记录项
                for item in history:
                    file_path = item['path']
                    file_name = item['name']
                    access_time = item['time']

                    # 检查文件是否存在
                    file_exists = os.path.exists(file_path)

                    # 创建列表项
                    display_text = f"{file_name} - {access_time}"
                    if not file_exists:
                        display_text += " (文件不存在)"

                    list_item = QListWidgetItem(display_text)
                    list_item.setData(Qt.ItemDataRole.UserRole, file_path)

                    # 如果文件不存在，使用灰色显示
                    if not file_exists:
                        list_item.setForeground(QColor(150, 150, 150))

                    self.listWidget.addItem(list_item)
            except Exception as e:
                self.listWidget.addItem(f"加载历史记录失败: {e}")
        else:
            self.listWidget.addItem("没有历史记录")

    def openHistoryItem(self, item):
        """打开选中的历史记录项"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.readWindow.openHistoryFile(file_path)

    def clearHistory(self):
        """清除所有历史记录"""
        history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")

        try:
            # 创建空的历史记录
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

            # 刷新显示
            self.loadHistory()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", f"清除历史记录失败: {e}")
