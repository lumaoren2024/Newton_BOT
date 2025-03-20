#!/bin/bash

# 定义变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/python-venv"
PYTHON_SCRIPT="bot.py"

# 检查 Python 是否可用
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装，请先安装 Python 3.8 或更高版本。"
    exit 1
fi

# 创建并激活虚拟环境
if [ ! -d "$VENV_PATH" ]; then
    echo "创建虚拟环境..."
    python3 -m venv "$VENV_PATH"
fi
source "$VENV_PATH/bin/activate"

# 安装依赖
echo "安装依赖..."
pip install --upgrade pip
pip install playwright
playwright install --force

# 检查 bot.py 是否存在
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "错误: $PYTHON_SCRIPT 不存在，请确保脚本文件在当前目录。"
    exit 1
fi

# 运行脚本
echo "运行 $PYTHON_SCRIPT..."
python "$PYTHON_SCRIPT"

# 退出虚拟环境
deactivate
