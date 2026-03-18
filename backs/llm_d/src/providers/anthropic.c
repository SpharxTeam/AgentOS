/**
 * @file anthropic.c
 * @brief Anthropic 适配器
 * @copyright (c) 2026 SPHARX. All Rights Reserved.
 */

#include "provider.h"
#include "logger.h"
#include <stdlib.h>
#include <string.h>
#include <errno.h>

typedef struct anthropic_ctx {
    char api_key[512];
    char api_base[512];
    char version[64];
    double timeout_sec;
    int max_retries;
    char** models;
    size_t model_count;
} anthropic_ctx_t;

/* 构建 Anthropic 请求体 */
static char* build_anthropic_request(const llm_request_config_t* cfg) {
    cJSON* root = cJSON_CreateObject();
    cJSON_AddStringToObject(root, "model", cfg->model);
    cJSON_AddNumberToObject(root, "temperature", cfg->temperature);
    if (cfg->max_tokens > 0) cJSON_AddNumberToObject(root, "max_tokens", cfg->max_tokens);
    if (cfg->stream) cJSON_AddBoolToObject(root, "stream", cfg->stream);

    // 分离 system 消息
    char* system = NULL;
    cJSON* messages = cJSON_CreateArray();
    for (size_t i = 0; i < cfg->message_count; i++) {
        if (strcmp(cfg->messages[i].role, "system") == 0) {
            system = strdup(cfg->messages[i].content);
        } else {
            cJSON* msg = cJSON_CreateObject();
            cJSON_AddStringToObject(msg, "role", cfg->messages[i].role);
            cJSON_AddStringToObject(msg, "content", cfg->messages[i].content);
            cJSON_AddItemToArray(messages, msg);
        }
    }
    if (system) {
        cJSON_AddStringToObject(root, "system", system);
        free(system);
    }
    cJSON_AddItemToObject(root, "messages", messages);

    char* json = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);
    return json;
}

/* 解析 Anthropic 响应 */
static int parse_anthropic_response(const char* body, llm_response_t** out) {
    cJSON* root = cJSON_Parse(body);
    if (!root) return -1;

    llm_response_t* resp = calloc(1, sizeof(llm_response_t));
    if (!resp) {
        cJSON_Delete(root);
        return -1;
    }

    cJSON* id = cJSON_GetObjectItem(root, "id");
    if (cJSON_IsString(id)) resp->id = strdup(id->valuestring);

    cJSON* model = cJSON_GetObjectItem(root, "model");
    if (cJSON_IsString(model)) resp->model = strdup(model->valuestring);

    // 提取内容
    cJSON* content_arr = cJSON_GetObjectItem(root, "content");
    if (cJSON_IsArray(content_arr) && cJSON_GetArraySize(content_arr) > 0) {
        cJSON* first = cJSON_GetArrayItem(content_arr, 0);
        cJSON* text = cJSON_GetObjectItem(first, "text");
        if (cJSON_IsString(text)) {
            resp->choice_count = 1;
            resp->choices = calloc(1, sizeof(llm_message_t));
            if (resp->choices) {
                ((char**)&resp->choices[0].role)[0] = strdup("assistant");
                ((char**)&resp->choices[0].content)[0] = strdup(text->valuestring);
            }
        }
    }

    cJSON* usage = cJSON_GetObjectItem(root, "usage");
    if (usage) {
        cJSON* in_tokens = cJSON_GetObjectItem(usage, "input_tokens");
        cJSON* out_tokens = cJSON_GetObjectItem(usage, "output_tokens");
        if (cJSON_IsNumber(in_tokens)) resp->prompt_tokens = (uint32_t)in_tokens->valuedouble;
        if (cJSON_IsNumber(out_tokens)) resp->completion_tokens = (uint32_t)out_tokens->valuedouble;
        resp->total_tokens = resp->prompt_tokens + resp->completion_tokens;
    }

    cJSON_Delete(root);
    *out = resp;
    return 0;
}

/* 流式处理 */
typedef struct anthropic_stream_ctx {
    llm_stream_callback_t cb;
    void* user_data;
    char* buffer;
    size_t buf_size;
} anthropic_stream_ctx_t;

static size_t anthropic_stream_write(void* contents, size_t size, size_t nmemb, void* userp) {
    anthropic_stream_ctx_t* sctx = userp;
    size_t realsize = size * nmemb;

    char* new_buf = realloc(sctx->buffer, sctx->buf_size + realsize + 1);
    if (!new_buf) return 0;
    sctx->buffer = new_buf;
    memcpy(sctx->buffer + sctx->buf_size, contents, realsize);
    sctx->buf_size += realsize;
    sctx->buffer[sctx->buf_size] = '\0';

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
            cJSON* root = cJSON_Parse(json_str);
            if (root) {
                const char* type = NULL;
                cJSON* type_item = cJSON_GetObjectItem(root, "type");
                if (cJSON_IsString(type_item)) type = type_item->valuestring;
                if (type && strcmp(type, "content_block_delta") == 0) {
                    cJSON* delta = cJSON_GetObjectItem(root, "delta");
                    if (delta) {
                        cJSON* text = cJSON_GetObjectItem(delta, "text");
                        if (cJSON_IsString(text) && text->valuestring) {
                            sctx->cb(text->valuestring, sctx->user_data);
                        }
                    }
                }
                cJSON_Delete(root);
            }
        }
        line_start = p + 1;
    }

    if (line_start > sctx->buffer) {
        size_t remaining = sctx->buf_size - (line_start - sctx->buffer);
        memmove(sctx->buffer, line_start, remaining);
        sctx->buf_size = remaining;
        sctx->buffer[remaining] = '\0';
    }
    return realsize;
}

static void* anthropic_init(const provider_config_t* cfg) {
    if (!cfg || !cfg->api_key) {
        errno = EINVAL;
        return NULL;
    }
    anthropic_ctx_t* ctx = calloc(1, sizeof(anthropic_ctx_t));
    if (!ctx) return NULL;

    strncpy(ctx->api_key, cfg->api_key, sizeof(ctx->api_key)-1);
    if (cfg->api_base) {
        strncpy(ctx->api_base, cfg->api_base, sizeof(ctx->api_base)-1);
    } else {
        snprintf(ctx->api_base, sizeof(ctx->api_base), "https://api.anthropic.com/v1");
    }
    snprintf(ctx->version, sizeof(ctx->version), "2023-06-01");
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

static void anthropic_destroy(void* vctx) {
    anthropic_ctx_t* ctx = vctx;
    if (!ctx) return;
    if (ctx->models) {
        for (size_t i = 0; i < ctx->model_count; i++) free(ctx->models[i]);
        free(ctx->models);
    }
    free(ctx);
}

static int anthropic_complete(void* vctx,
                              const llm_request_config_t* config,
                              llm_response_t** out) {
    anthropic_ctx_t* ctx = vctx;
    if (!ctx || !config || !out) {
        errno = EINVAL;
        return -1;
    }

    char* body = build_anthropic_request(config);
    if (!body) return -1;

    char url[1024];
    snprintf(url, sizeof(url), "%s/messages", ctx->api_base);

    struct curl_slist* headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    headers = curl_slist_append(headers, "anthropic-version: 2023-06-01");
    char auth_hdr[512];
    snprintf(auth_hdr, sizeof(auth_hdr), "x-api-key: %s", ctx->api_key);
    headers = curl_slist_append(headers, auth_hdr);

    http_buffer_t* resp_buf = NULL;
    long http_code = 0;
    int ret = provider_http_post(url, headers, body,
                                 ctx->timeout_sec, ctx->max_retries,
                                 &resp_buf, &http_code);
    curl_slist_free_all(headers);
    free(body);

    if (ret != 0) {
        AGENTOS_LOG_ERROR("anthropic: HTTP request failed");
        return -1;
    }

    if (http_code != 200) {
        AGENTOS_LOG_ERROR("anthropic: HTTP error %ld", http_code);
        provider_http_buffer_free(resp_buf);
        return -1;
    }

    ret = parse_anthropic_response(resp_buf->data, out);
    provider_http_buffer_free(resp_buf);
    return ret;
}

static int anthropic_complete_stream(void* vctx,
                                     const llm_request_config_t* config,
                                     llm_stream_callback_t cb,
                                     llm_response_t** out) {
    anthropic_ctx_t* ctx = vctx;
    if (!ctx || !config || !cb) {
        errno = EINVAL;
        return -1;
    }

    llm_request_config_t stream_cfg = *config;
    stream_cfg.stream = 1;
    char* body = build_anthropic_request(&stream_cfg);
    if (!body) return -1;

    char url[1024];
    snprintf(url, sizeof(url), "%s/messages", ctx->api_base);

    struct curl_slist* headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    headers = curl_slist_append(headers, "anthropic-version: 2023-06-01");
    char auth_hdr[512];
    snprintf(auth_hdr, sizeof(auth_hdr), "x-api-key: %s", ctx->api_key);
    headers = curl_slist_append(headers, auth_hdr);

    CURL* curl = curl_easy_init();
    if (!curl) {
        curl_slist_free_all(headers);
        free(body);
        return -1;
    }

    anthropic_stream_ctx_t sctx = {0};
    sctx.cb = cb;
    sctx.user_data = config->user_data;

    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_POST, 1L);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, anthropic_stream_write);
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
        AGENTOS_LOG_ERROR("anthropic: stream HTTP request failed: %s", curl_easy_strerror(res));
        free(sctx.buffer);
        return -1;
    }
    if (http_code != 200) {
        AGENTOS_LOG_ERROR("anthropic: stream HTTP error %ld", http_code);
        free(sctx.buffer);
        return -1;
    }

    if (out) *out = NULL;
    free(sctx.buffer);
    return 0;
}

static const provider_ops_t anthropic_ops = {
    .init = anthropic_init,
    .destroy = anthropic_destroy,
    .complete = anthropic_complete,
    .complete_stream = anthropic_complete_stream,
};

const provider_ops_t* provider_get_anthropic_ops(void) {
    return &anthropic_ops;
}