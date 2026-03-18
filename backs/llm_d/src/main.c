/**
 * @file main.c
 * @brief LLM 服务入口
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#include "llm_service.h"
#include "logger.h"
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>

static llm_service_t* g_service = NULL;

static void signal_handler(int sig) {
    if (sig == SIGINT || sig == SIGTERM) {
        AGENTOS_LOG_INFO("Received signal %d, shutting down...", sig);
        if (g_service) {
            llm_service_destroy(g_service);
            g_service = NULL;
        }
        exit(0);
    }
}

int main(int argc, char** argv) {
    const char* config_path = "llm_config.yaml";
    if (argc > 1) config_path = argv[1];

    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    AGENTOS_LOG_INFO("LLM service starting with config %s", config_path);
    g_service = llm_service_create(config_path);
    if (!g_service) {
        AGENTOS_LOG_ERROR("Failed to create LLM service");
        return 1;
    }

    // TODO: 启动 RPC 服务器（如使用 HTTP 或 gRPC），接受外部请求
    // 当前保持运行
    AGENTOS_LOG_INFO("LLM service started. Press Ctrl+C to stop.");
    while (1) {
        sleep(1);
    }

    return 0;
}