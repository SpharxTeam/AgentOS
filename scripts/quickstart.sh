#!/bin/bash
# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 快速启动示例

set -e

echo "AgentOS Quickstart"
echo "=================="

# 检查是否已安装
if ! command -v poetry &> /dev/null; then
    echo "Installing AgentOS first..."
    ./scripts/install.sh
fi

# 初始化配置
python scripts/init_config.py

# 运行示例
cd examples/ecommerce_dev
./run.sh