@echo off

REM 定义变量
set SCRIPT_DIR=%~dp0
set VENV_PATH=%SCRIPT_DIR%python-venv
set PYTHON_SCRIPT=bot.py

REM 检查 Python 是否可用
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误: Python 未安装，请先安装 Python 3.8 或更高版本。
    exit /b 1
)

REM 创建并激活虚拟环境
if not exist "%VENV_PATH%" (
    echo 创建虚拟环境...
    python -m venv "%VENV_PATH%"
)
call "%VENV_PATH%\Scripts\activate.bat"

REM 安装依赖
echo 安装依赖...
pip install --upgrade pip
pip install playwright
playwright install --force

REM 检查 bot.py 是否存在
if not exist "%PYTHON_SCRIPT%" (
    echo 错误: %PYTHON_SCRIPT% 不存在，请确保脚本文件在当前目录。
    exit /b 1
)

REM 运行脚本
echo 运行 %PYTHON_SCRIPT%...
python "%PYTHON_SCRIPT%"

REM 退出虚拟环境
call deactivate
