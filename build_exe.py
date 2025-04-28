# -*- coding: utf-8 -*-
"""
乐跑系统打包脚本
使用PyInstaller将Flask应用打包成exe可执行文件
"""

import PyInstaller.__main__
import os
import shutil

# 获取当前目录
base_dir = os.path.abspath(os.path.dirname(__file__))

# 定义需要包含的数据文件
additional_files = [
    ('static', 'static'),
    ('templates', 'templates'),
    ('index.html', '.'),
]

# 定义PyInstaller参数
pyinstaller_args = [
    'app.py',  # 主程序入口
    '--name=乐跑系统',  # 生成的exe名称
    '--onefile',  # 打包成单个exe文件
    '--windowed',  # 使用windowed替代noconsole，确保GUI应用正确启动
    '--icon=static/favicon.ico' if os.path.exists(os.path.join(base_dir, 'static/favicon.ico')) else None,  # 图标
    '--clean',  # 清理临时文件
    '--noconfirm',  # 不询问确认
    f'--distpath={os.path.join(base_dir, "dist")}',  # 输出目录
    f'--workpath={os.path.join(base_dir, "build")}',  # 工作目录
    f'--specpath={base_dir}',  # spec文件目录
    '--add-data={}:{}'.format(os.path.join(base_dir, 'static'), 'static'),  # 添加静态文件
    '--add-data={}:{}'.format(os.path.join(base_dir, 'templates'), 'templates'),  # 添加模板文件
    '--add-data={}:{}'.format(os.path.join(base_dir, 'index.html'), '.'),  # 添加主页文件
]

# 移除None值
pyinstaller_args = [arg for arg in pyinstaller_args if arg is not None]

# 打印开始信息
print("开始打包乐跑系统...")
print(f"入口文件: app.py")
print(f"输出目录: {os.path.join(base_dir, 'dist')}")

# 运行PyInstaller
try:
    PyInstaller.__main__.run(pyinstaller_args)
    print("\n打包完成!")
    print(f"可执行文件位置: {os.path.join(base_dir, 'dist', '乐跑系统.exe')}")
except Exception as e:
    print(f"打包过程中出错: {e}")
