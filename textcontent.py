from PySide6.QtGui import QFont, QMouseEvent, QTextCursor
from PySide6.QtWidgets import QTextEdit, QApplication
from filecache import FileCache
import sys


class TextContent(QTextEdit):
    def __init__(self, fileName, config):
        super().__init__()
        print(f"[DEBUG] 初始化 TextContent，文件名：{fileName}")
        self.file_cache = FileCache()
        self.initText(fileName, config)

    def initText(self, fileName, config):
        print(f"[DEBUG] 开始初始化文本内容")
        # 重置文档状态
        print("[DEBUG] 清理文档状态")
        self.clear()
        self.document().clear()
        self.document().clearUndoRedoStacks()

        # 设置字体大小
        font = QFont()
        font.setPointSize(int(config.get('settings', 'fontSize')))
        self.setFont(font)

        # 设置背景色和文本颜色
        self.setStyleSheet('QTextEdit { background-color: white; color: black; padding: 10px; line-height: 150%; }')
        # 设置为只读模式
        self.setReadOnly(True)

        # 尝试从缓存获取文本
        print(f"[DEBUG] 尝试从缓存获取文本：{fileName}")
        content = self.file_cache.get_cached_content(fileName)
        if content is None:
            print("[DEBUG] 缓存未命中，开始缓存文件")
            # 如果缓存中不存在，则缓存文件并读取
            self.file_cache.cache_file(fileName)
            content = self.file_cache.get_cached_content(fileName)

        if content:
            print(f"[DEBUG] 获取到文本内容，长度：{len(content)}")
            # 分段加载文本内容
            self.loadTextInChunks(content)
        else:
            print("[DEBUG] 无法读取文件内容")
            self.setPlainText("无法读取文件内容")

    def loadTextInChunks(self, content: str, chunk_size: int = 5000):
        print("[DEBUG] 开始分段加载文本内容")
        sys.stdout.flush()
        # 确保完全清空当前文本
        self.clear()
        self.document().clear()

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        # 分段处理文本
        start = 0
        chunk_count = 0
        while start < len(content):
            # 获取当前段的文本
            chunk = content[start:start + chunk_size]

            # 确保在完整的段落处分割
            if start + chunk_size < len(content):
                last_newline = chunk.rfind('\n')
                if last_newline != -1:
                    chunk = chunk[:last_newline + 1]
                    start += last_newline + 1
                else:
                    start += chunk_size
            else:
                start += len(chunk)

            # 插入文本段
            cursor.insertText(chunk)
            chunk_count += 1
            print(f"[DEBUG] 已加载第 {chunk_count} 段文本，当前位置：{start}/{len(content)}")

            # 处理事件循环，避免界面卡顿
            QApplication.processEvents()

        print("[DEBUG] 文本加载完成，移动光标到开始位置")
        # 将光标移动到开始位置
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.setTextCursor(cursor)

    # 重写点击事件
    def mousePressEvent(self, event: QMouseEvent) -> None:
        event.ignore()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        event.ignore()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        event.ignore()

    def __del__(self):
        print("[DEBUG] TextContent 被销毁")
