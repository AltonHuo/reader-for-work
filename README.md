# 阅读器

一个基于 PySide6 开发的简单阅读器应用程序，提供文件阅读和设置管理功能。

## 功能特点

- 文件阅读：支持文件浏览和阅读
- 设置管理：提供个性化设置选项
- 界面简洁：采用选项卡式设计，操作直观
- 中文界面：完全中文化的用户界面

## 环境要求

- Python 3.6 或更高版本
- Windows/macOS/Linux 操作系统

## 安装步骤

1. 克隆或下载项目到本地

2. 创建并激活虚拟环境（推荐）
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. 安装依赖包
   ```bash
   pip install -r requirements.txt
   ```

## 运行应用

```bash
# 直接运行 Python 脚本
python app.py
```

## Windows 打包说明

1. 确保已安装所有依赖
   ```bash
   pip install -r requirements.txt
   ```

2. 使用 PyInstaller 打包
   ```bash
   # 使用现有的 spec 文件打包
   pyinstaller app.spec
   ```

   或者从头开始打包：
   ```bash
   pyinstaller --name="阅读器" \
               --windowed \
               --icon=icon.ico \
               --noconsole \
               app.py
   ```

3. 打包完成后，可执行文件将位于 `dist` 目录中

## 注意事项

- 首次运行时会自动创建配置文件
- 程序会自动保存用户设置
- 关闭程序时会自动保存当前配置

## 依赖列表

- PySide6 >= 6.5.0：Qt for Python 框架
- PyInstaller >= 5.13.0：用于打包 Python 应用
