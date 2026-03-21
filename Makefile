# AgentOS Makefile

.PHONY: help build clean test install docs lint format setup validate quickstart

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
COLOR_RESET=\033[0m
COLOR_GREEN=\033[32m
COLOR_YELLOW=\033[33m
COLOR_BLUE=\033[34m

# 变量定义
BUILD_DIR ?= build
CMAKE_BUILD_TYPE ?= Release
PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

help: ## 显示帮助信息
	@echo "$(COLOR_BLUE)AgentOS Makefile$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_GREEN)可用目标:$$(COLOR_RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(COLOR_YELLOW)-16s$(COLOR_RESET) %s\n", $$1, $$2}'
	@echo ""

setup: ## 初始化开发环境
	@echo "$(COLOR_GREEN)正在设置 AgentOS 开发环境...$(COLOR_RESET)"
	@cp -n .env.example .env || true
	@$(PYTHON) scripts/init_config.py
	@echo "$(COLOR_GREEN)✓ 环境设置完成$(COLOR_RESET)"

build: ## 编译 C++ 内核
	@echo "$(COLOR_GREEN)正在构建 AgentOS 内核...$(COLOR_RESET)"
	@mkdir -p $(BUILD_DIR)
	@cd $(BUILD_DIR) && cmake ../coreadd \
		-DCMAKE_BUILD_TYPE=$(CMAKE_BUILD_TYPE) \
		-DBUILD_TESTS=ON \
		-DENABLE_TRACING=ON
	@cmake --build $(BUILD_DIR) --parallel $$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
	@echo "$(COLOR_GREEN)✓ 构建完成$(COLOR_RESET)"

test: ## 运行所有测试
	@echo "$(COLOR_GREEN)正在运行测试...$(COLOR_RESET)"
	@cd $(BUILD_DIR) && ctest --output-on-failure
	@echo "$(COLOR_GREEN)✓ 测试完成$(COLOR_RESET)"

test-unit: ## 运行单元测试
	@echo "$(COLOR_GREEN)正在运行单元测试...$(COLOR_RESET)"
	@cd $(BUILD_DIR) && ctest -R unit --output-on-failure
	@echo "$(COLOR_GREEN)✓ 单元测试完成$(COLOR_RESET)"

test-integration: ## 运行集成测试
	@echo "$(COLOR_GREEN)正在运行集成测试...$(COLOR_RESET)"
	@cd $(BUILD_DIR) && ctest -R integration --output-on-failure
	@echo "$(COLOR_GREEN)✓ 集成测试完成$(COLOR_RESET)"

benchmark: ## 运行性能基准测试
	@echo "$(COLOR_GREEN)正在运行性能基准测试...$(COLOR_RESET)"
	@$(PYTHON) scripts/benchmark.py
	@echo "$(COLOR_GREEN)✓ 基准测试完成$(COLOR_RESET)"

clean: ## 清理构建产物
	@echo "$(COLOR_GREEN)正在清理构建产物...$(COLOR_RESET)"
	@rm -rf $(BUILD_DIR)
	@rm -rf dist/
	@rm -rf *.egg-info
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(COLOR_GREEN)✓ 清理完成$(COLOR_RESET)"

install: ## 安装依赖和构建
	@echo "$(COLOR_GREEN)正在安装依赖...$(COLOR_RESET)"
	@$(PIP) install -e .
	@echo "$(COLOR_GREEN)✓ 依赖安装完成$(COLOR_RESET)"

install-dev: ## 安装开发依赖
	@echo "$(COLOR_GREEN)正在安装开发依赖...$(COLOR_RESET)"
	@$(PIP) install -e ".[dev]"
	@pre-commit install
	@echo "$(COLOR_GREEN)✓ 开发环境配置完成$(COLOR_RESET)"

docs: ## 生成文档
	@echo "$(COLOR_GREEN)正在生成文档...$(COLOR_RESET)"
	@$(PYTHON) scripts/generate_docs.py
	@echo "$(COLOR_GREEN)✓ 文档生成完成$(COLOR_RESET)"

lint: ## 代码检查
	@echo "$(COLOR_GREEN)正在检查代码...$(COLOR_RESET)"
	@python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@python -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "$(COLOR_GREEN)✓ 代码检查完成$(COLOR_RESET)"

format: ## 格式化代码
	@echo "$(COLOR_GREEN)正在格式化代码...$(COLOR_RESET)"
	@python -m black . --exclude '/(\.venv|venv|build|dist)/'
	@python -m isort . --profile black
	@echo "$(COLOR_GREEN)✓ 代码格式化完成$(COLOR_RESET)"

validate: ## 验证环境配置
	@echo "$(COLOR_GREEN)正在验证环境配置...$(COLOR_RESET)"
	@./validate.sh
	@echo "$(COLOR_GREEN)✓ 环境验证完成$(COLOR_RESET)"

quickstart: ## 一键快速启动
	@echo "$(COLOR_GREEN)正在启动快速体验...$(COLOR_RESET)"
	@./quickstart.sh
	@echo "$(COLOR_GREEN)✓ 快速体验完成$(COLOR_RESET)"

release: ## 创建新版本
	@echo "$(COLOR_GREEN)正在创建新版本...$(COLOR_RESET)"
	@$(PYTHON) scripts/update_version.py
	@echo "$(COLOR_GREEN)✓ 版本更新完成$(COLOR_RESET)"

docker-build: ## 构建 Docker 镜像
	@echo "$(COLOR_GREEN)正在构建 Docker 镜像...$(COLOR_RESET)"
	@docker-compose build
	@echo "$(COLOR_GREEN)✓ Docker 镜像构建完成$(COLOR_RESET)"

docker-up: ## 启动 Docker 容器
	@echo "$(COLOR_GREEN)正在启动 Docker 容器...$(COLOR_RESET)"
	@docker-compose up -d
	@echo "$(COLOR_GREEN)✓ Docker 容器已启动$(COLOR_RESET)"

docker-down: ## 停止 Docker 容器
	@echo "$(COLOR_GREEN)正在停止 Docker 容器...$(COLOR_RESET)"
	@docker-compose down
	@echo "$(COLOR_GREEN)✓ Docker 容器已停止$(COLOR_RESET)"

all: clean setup build test install docs ## 执行完整构建流程
	@echo "$(COLOR_GREEN)✓ 完整构建流程完成$(COLOR_RESET)"
