/**
 * @file main.c
 * @brief Habitat 可执行入口
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#include "habitat.h"
#include "logger.h"
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

static agentos_habitat_server_t* g_server = NULL;

static void signal_handler(int sig) {
    if (sig == SIGINT || sig == SIGTERM) {
        AGENTOS_LOG_INFO("Received signal %d, shutting down...", sig);
        if (g_server) {
            agentos_habitat_stop(g_server);
        }
    }
}

int main(int argc, char** argv) {
    // 注册信号处理
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 可以解析命令行参数覆盖配置，这里简化
    agentos_habitat_config_t config = {
        .http_host = "0.0.0.0",
        .http_port = 18789,
        .ws_host = "0.0.0.0",
        .ws_port = 18790,
        .enable_stdio = 1,
        .max_sessions = 1000,
        .session_timeout_sec = 3600,
        .health_check_interval_sec = 30,
        .metrics_path = "/metrics",
    };

    agentos_habitat_server_t* server = NULL;
    if (agentos_habitat_start(&config, &server) != 0) {
        AGENTOS_LOG_ERROR("Failed to start Habitat server");
        return 1;
    }
    g_server = server;

    AGENTOS_LOG_INFO("Habitat server started on http://%s:%d", config.http_host, config.http_port);
    agentos_habitat_wait(server);
    agentos_habitat_destroy(server);
    AGENTOS_LOG_INFO("Habitat server stopped");
    return 0;
}