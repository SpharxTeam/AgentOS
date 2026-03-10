#!/bin/bash
# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# AgentOS 一键安装脚本（Linux/macOS）

set -e

echo "Installing AgentOS..."

# 检测Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
if [[ $(echo "$PYTHON_VERSION < 3.9" | bc) -eq 1 ]]; then
    echo "Error: Python 3.9+ required, found $PYTHON_VERSION"
    exit 1
fi

# 安装依赖
pip install --upgrade pip
pip install poetry

# 安装项目
poetry install

# 初始化配置
cp .env.example .env
echo "Please edit .env to add your API keys."

# 创建必要目录
mkdir -p data/workspace data/registry data/logs

echo "AgentOS installed successfully!"
echo "Run 'poetry run agentos gateway start' to start the service."