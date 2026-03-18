/**
 * @file openai.c
 * @brief OpenAI 提供商适配器
 * @copyright (c) 2026 SPHARX. All Rights Reserved.
 */

#include "provider.h"
#include "logger.h"
#include <stdlib.h>
#include <string.h>
#include <errno.h>

typedef struct openai_ctx {
    char api_key[256];
    char api_base[256];
    char organization[128];
    double timeout_sec;
    int max_retries;
    char** models;
    size_t model_count;
} openai_ctx_t;

static void* openai_init(const provider_config_t* cfg) {
    if (!cfg || !cfg->api_key) {
        errno = EINVAL;
        return NULL;
    }

    openai_ctx_t* ctx = calloc(1, sizeof(openai_ctx_t));
    if (!ctx) return NULL;

    strncpy(ctx->api_key, cfg->api_key, sizeof(ctx->api_key)-1);
    if (cfg->api_base) {
        strncpy(ctx->api_base, cfg->api_base, sizeof(ctx->api_base)-1);
    } else {
        snprintf(ctx->api_base, sizeof(ctx->api_base), "https://api.openai.com/v1");
    }
    if (cfg->organization) {
        strncpy(ctx->organization, cfg->organization, sizeof(ctx->organization)-1);
    }
    ctx->timeout_sec = cfg->timeout_sec > 0 ? cfg->timeout_sec : 30.0;
    ctx->max_retries = cfg->max_retries > 0 ? cfg->max_retries : 3;

    if (cfg->models && cfg->model_count > 0) {
        ctx->models = calloc(cfg->model_count + 1, sizeof(char*));
        if (!ctx->models) {
            free(ctx);
            return NULL;
        }
        for (size_t i = 0; i < cfg->model_count; i++) {
            ctx->models[i] = strdup(cfg->models[i]);
            if (!ctx->models[i]) {
                for (size_t j = 0; j < i; j++) free(ctx->models[j]);
                free(ctx->models);
                free(ctx);
                return NULL;
            }
        }
        ctx->model_count = cfg->model_count;
    }
    return ctx;
}

static void openai_destroy(void* vctx) {
    openai_ctx_t* ctx = vctx;
    if (!ctx) return;
    if (ctx->models) {
        for (size_t i = 0; i < ctx->model_count; i++) free(ctx->models[i]);
        free(ctx->models);
    }
    free(ctx);
}

static int openai_complete(void* vctx,
                           const llm_request_config_t* config,
                           llm_response_t** out) {
    openai_ctx_t* ctx = vctx;
    if (!ctx || !config || !out) {
        errno = EINVAL;
        return -1;
    }

    char* body = provider_build_openai_request(config);
    if (!body) return -1;

    char url[1024];
    snprintf(url, sizeof(url), "%s/chat/completions", ctx->api_base);

    struct curl_slist* headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    char auth_hdr[512];
    snprintf(auth_hdr, sizeof(auth_hdr), "Authorization: Bearer %s", ctx->api_key);
    headers = curl_slist_append(headers, auth_hdr);
    if (ctx->organization[0]) {
        char org_hdr[512];
        snprintf(org_hdr, sizeof(org_hdr), "OpenAI-Organization: %s", ctx->organization);
        headers = curl_slist_append(headers, org_hdr);
    }

    http_buffer_t* resp_buf = NULL;
    long http_code = 0;
    int ret = provider_http_post(url, headers, body,
                                 ctx->timeout_sec, ctx->max_retries,
                                 &resp_buf, &http_code);
    curl_slist_free_all(headers);
    free(body);

    if (ret != 0) {
        AGENTOS_LOG_ERROR("openai: HTTP request failed");
        return -1;
    }

    if (http_code != 200) {
        char* err_msg = provider_extract_openai_error(resp_buf->data);
        AGENTOS_LOG_ERROR("openai: HTTP %ld: %s", http_code, err_msg ? err_msg : "unknown");
        free(err_msg);
        provider_http_buffer_free(resp_buf);
        errno = EIO;
        return -1;
    }

    ret = provider_parse_openai_response(resp_buf->data, out);
    provider_http_buffer_free(resp_buf);
    return ret;
}

/* ---------- 流式实现 ---------- */
typedef struct stream_ctx {
    llm_stream_callback_t cb;
    void* user_data;
    char* buffer;
    size_t buf_size;
} stream_ctx_t;

static size_t stream_write_cb(void* contents, size_t size, size_t nmemb, void* userp) {
    stream_ctx_t* sctx = userp;
    size_t realsize = size * nmemb;
    char* data = contents;

    char* new_buf = realloc(sctx->buffer, sctx->buf_size + realsize + 1);
    if (!new_buf) return 0;
    sctx->buffer = new_buf;
    memcpy(sctx->buffer + sctx->buf_size, data, realsize);
    sctx->buf_size += realsize;
    sctx->buffer[sctx->buf_size] = '\0';

    // 按行分割处理
    char* line_start = sctx->buffer;
    char* p;
    while ((p = strstr(line_start, "\n")) != NULL) {
        *p = '\0';
        char* line = line_start;

        if (strlen(line) == 0) {
            line_start = p + 1;
            continue;
        }

        if (strncmp(line, "data: ", 6) == 0) {
            char* json_str = line + 6;
            if (strcmp(json_str, "[DONE]") == 0) {
                line_start = p + 1;
                continue;
            }
            cJSON* root = cJSON_Parse(json_str);
            if (root) {
                cJSON* choices = cJSON_GetObjectItem(root, "choices");
                if (cJSON_IsArray(choices) && cJSON_GetArraySize(choices) > 0) {
                    cJSON* choice = cJSON_GetArrayItem(choices, 0);
                    cJSON* delta = cJSON_GetObjectItem(choice, "delta");
                    if (delta) {
                        cJSON* content = cJSON_GetObjectItem(delta, "content");
                        if (cJSON_IsString(content) && content->valuestring) {
                            sctx->cb(content->valuestring, sctx->user_data);
                        }
                    }
                }
                cJSON_Delete(root);
            }
        }
        line_start = p + 1;
    }

    // 将未处理完的部分移到缓冲区开头
    if (line_start > sctx->buffer) {
        size_t remaining = sctx->buf_size - (line_start - sctx->buffer);
        memmove(sctx->buffer, line_start, remaining);
        sctx->buf_size = remaining;
        sctx->buffer[remaining] = '\0';
    }
    return realsize;
}

static int openai_complete_stream(void* vctx,
                                  const llm_request_config_t* config,
                                  llm_stream_callback_t cb,
                                  llm_response_t** out) {
    openai_ctx_t* ctx = vctx;
    if (!ctx || !config || !cb) {
        errno = EINVAL;
        return -1;
    }

    // 强制启用流式
    llm_request_config_t stream_cfg = *config;
    stream_cfg.stream = 1;
    char* body = provider_build_openai_request(&stream_cfg);
    if (!body) return -1;

    char url[1024];
    snprintf(url, sizeof(url), "%s/chat/completions", ctx->api_base);

    struct curl_slist* headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    char auth_hdr[512];
    snprintf(auth_hdr, sizeof(auth_hdr), "Authorization: Bearer %s", ctx->api_key);
    headers = curl_slist_append(headers, auth_hdr);
    if (ctx->organization[0]) {
        char org_hdr[512];
        snprintf(org_hdr, sizeof(org_hdr), "OpenAI-Organization: %s", ctx->organization);
        headers = curl_slist_append(headers, org_hdr);
    }

    CURL* curl = curl_easy_init();
    if (!curl) {
        curl_slist_free_all(headers);
        free(body);
        AGENTOS_LOG_ERROR("openai: curl_easy_init failed");
        return -1;
    }

    stream_ctx_t sctx = {0};
    sctx.cb = cb;
    sctx.user_data = config->user_data;

    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_POST, 1L);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, stream_write_cb);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &sctx);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, (long)ctx->timeout_sec);
    curl_easy_setopt(curl, CURLOPT_NOSIGNAL, 1L);

    CURLcode res = curl_easy_perform(curl);
    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    curl_easy_cleanup(curl);
    curl_slist_free_all(headers);
    free(body);

    if (res != CURLE_OK) {
        AGENTOS_LOG_ERROR("openai: stream HTTP request failed: %s", curl_easy_strerror(res));
        free(sctx.buffer);
        return -1;
    }
    if (http_code != 200) {
        AGENTOS_LOG_ERROR("openai: stream HTTP error %ld", http_code);
        free(sctx.buffer);
        return -1;
    }

    if (out) *out = NULL;  // 流式不返回最终响应
    free(sctx.buffer);
    return 0;
}

static const provider_ops_t openai_ops = {
    .init = openai_init,
    .destroy = openai_destroy,
    .complete = openai_complete,
    .complete_stream = openai_complete_stream,
};

const provider_ops_t* provider_get_openai_ops(void) {
    return &openai_ops;
}