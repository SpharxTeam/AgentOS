/**
 * @file deepseek.c
 * @brief DeepSeek 提供商适配器
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#include "provider.h"
#include "logger.h"
#include <stdlib.h>
#include <string.h>

typedef struct deepseek_context {
    char api_key[512];
    char api_base[512];
    double timeout_sec;
    int max_retries;
    char** models;
    size_t model_count;
} deepseek_context_t;

static void* deepseek_init(const provider_config_t* config) {
    if (!config || !config->api_key) {
        AGENTOS_LOG_ERROR("deepseek: missing api_key");
        return NULL;
    }

    deepseek_context_t* ctx = (deepseek_context_t*)calloc(1, sizeof(deepseek_context_t));
    if (!ctx) return NULL;

    strncpy(ctx->api_key, config->api_key, sizeof(ctx->api_key)-1);
    if (config->api_base) {
        strncpy(ctx->api_base, config->api_base, sizeof(ctx->api_base)-1);
    } else {
        strcpy(ctx->api_base, "https://api.deepseek.com/v1");
    }
    ctx->timeout_sec = config->timeout_sec > 0 ? config->timeout_sec : 30.0;
    ctx->max_retries = config->max_retries;

    if (config->models && config->model_count > 0) {
        ctx->models = (char**)calloc(config->model_count + 1, sizeof(char*));
        if (ctx->models) {
            for (size_t i = 0; i < config->model_count; i++) {
                ctx->models[i] = strdup(config->models[i]);
                if (!ctx->models[i]) {
                    for (size_t j = 0; j < i; j++) free(ctx->models[j]);
                    free(ctx->models);
                    free(ctx);
                    return NULL;
                }
            }
            ctx->model_count = config->model_count;
        }
    }
    return ctx;
}

static void deepseek_destroy(void* ctx_ptr) {
    deepseek_context_t* ctx = (deepseek_context_t*)ctx_ptr;
    if (!ctx) return;
    if (ctx->models) {
        for (size_t i = 0; i < ctx->model_count; i++) free(ctx->models[i]);
        free(ctx->models);
    }
    free(ctx);
}

/* 复用 OpenAI 的构建函数 */
extern char* build_request_body(const llm_request_config_t* config);
extern int parse_response_body(const char* body, llm_response_t** out_response);

static int deepseek_complete(void* ctx_ptr,
                             const llm_request_config_t* config,
                             llm_response_t** out_response) {
    deepseek_context_t* ctx = (deepseek_context_t*)ctx_ptr;
    if (!ctx || !config || !out_response) return -1;

    char* request_body = build_request_body(config);
    if (!request_body) return -1;

    char url[1024];
    snprintf(url, sizeof(url), "%s/chat/completions", ctx->api_base);

    struct curl_slist* headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    char auth_header[512];
    snprintf(auth_header, sizeof(auth_header), "Authorization: Bearer %s", ctx->api_key);
    headers = curl_slist_append(headers, auth_header);

    http_buffer_t* resp_buf = NULL;
    long http_code = 0;
    int ret = provider_http_post(url, headers, request_body, ctx->timeout_sec, &resp_buf, &http_code);
    curl_slist_free_all(headers);
    free(request_body);

    if (ret != 0) {
        AGENTOS_LOG_ERROR("deepseek: HTTP request failed");
        return -1;
    }

    if (http_code != 200) {
        AGENTOS_LOG_ERROR("deepseek: HTTP error %ld", http_code);
        provider_http_buffer_free(resp_buf);
        return -1;
    }

    ret = parse_response_body(resp_buf->data, out_response);
    provider_http_buffer_free(resp_buf);
    return ret;
}

static int deepseek_complete_stream(void* ctx,
                                    const llm_request_config_t* config,
                                    llm_stream_callback_t callback,
                                    llm_response_t** out_response) {
    AGENTOS_LOG_ERROR("deepseek: streaming not implemented");
    return -1;
}

static const provider_ops_t deepseek_ops = {
    .init = deepseek_init,
    .destroy = deepseek_destroy,
    .complete = deepseek_complete,
    .complete_stream = deepseek_complete_stream,
};

const provider_ops_t* provider_get_deepseek_ops(void) {
    return &deepseek_ops;
}