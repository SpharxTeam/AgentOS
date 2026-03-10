# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# AgentOS 一键安装脚本（Windows PowerShell）

Write-Host "Installing AgentOS..." -ForegroundColor Green

# 检测Python版本
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python (\d+)\.(\d+)") {
    $major = $matches[1]
    $minor = $matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
        Write-Host "Error: Python 3.9+ required, found $major.$minor" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Error: Python not found" -ForegroundColor Red
    exit 1
}

# 安装依赖
pip install --upgrade pip
pip install poetry

# 安装项目
poetry install

# 初始化配置
Copy-Item .env.example .env
Write-Host "Please edit .env to add your API keys." -ForegroundColor Yellow

# 创建必要目录
New-Item -ItemType Directory -Force -Path data\workspace, data\registry, data\logs | Out-Null

Write-Host "AgentOS installed successfully!" -ForegroundColor Green
Write-Host "Run 'poetry run agentos gateway start' to start the service." -ForegroundColor Cyan