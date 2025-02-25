import os
import tempfile
from typing import Dict, Optional


class FileCache:
    def __init__(self, max_cache_size: int = 5):
        """初始化文件缓存管理器
        
        Args:
            max_cache_size: 最大缓存文件数量
        """
        self.max_cache_size = max_cache_size
        self.cache_dir = tempfile.mkdtemp(prefix='reader_cache_')
        self.cache_files: Dict[str, str] = {}
        self.cache_order: list = []

    def get_cached_content(self, file_path: str) -> Optional[str]:
        """获取缓存的文件内容
        
        Args:
            file_path: 原始文件路径
            
        Returns:
            缓存的文件内容，如果不存在则返回 None
        """
        if file_path in self.cache_files:
            cache_path = self.cache_files[file_path]
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return None
        return None

    def cache_file(self, file_path: str) -> None:
        """缓存文件内容
        
        Args:
            file_path: 需要缓存的文件路径
        """
        if file_path in self.cache_files:
            return

        # 如果缓存已满，删除最早的缓存
        if len(self.cache_files) >= self.max_cache_size:
            oldest_file = self.cache_order.pop(0)
            cache_path = self.cache_files.pop(oldest_file)
            try:
                os.remove(cache_path)
            except:
                pass

        # 创建新的缓存文件
        cache_path = os.path.join(self.cache_dir,
                                  f'cache_{len(self.cache_files)}')
        try:
            # 使用分块读取来处理大文件
            with open(file_path, 'r', encoding='utf-8') as src, \
                    open(cache_path, 'w', encoding='utf-8') as dst:
                while True:
                    chunk = src.read(8192)  # 8KB 的块大小
                    if not chunk:
                        break
                    dst.write(chunk)

            self.cache_files[file_path] = cache_path
            self.cache_order.append(file_path)
        except:
            pass

    def clear_cache(self) -> None:
        """清理所有缓存文件"""
        for cache_path in self.cache_files.values():
            try:
                os.remove(cache_path)
            except:
                pass
        try:
            os.rmdir(self.cache_dir)
        except:
            pass
        self.cache_files.clear()
        self.cache_order.clear()

    def __del__(self):
        """析构时清理缓存"""
        self.clear_cache()
