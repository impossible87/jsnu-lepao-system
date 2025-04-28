@echo off
chcp 65001 > nul
echo ===================================
echo        乐跑系统打包工具
echo ===================================
echo.

echo 正在检查Python环境...
python --version
if %ERRORLEVEL% neq 0 (
    echo [错误] 未检测到Python环境，请安装Python 3.6+
    pause
    exit /b
)

echo.
echo 正在安装/更新必要的依赖...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [警告] 依赖安装可能不完整，继续执行可能会失败
    pause
)

echo.
echo 开始打包程序...
python build_exe.py

if %ERRORLEVEL% neq 0 (
    echo [错误] 打包过程中出现错误
) else (
    echo.
    echo 打包完成！
    echo 可执行文件位于 dist\乐跑系统.exe
)

echo.
echo 按任意键退出...
pause > nul
