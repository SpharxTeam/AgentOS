/**
 * @file service.c
 * @brief LLM 服务核心业务逻辑
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#include "llm_service.h"
#include "provider.h"
#include "cache.h"
#include "cost_tracker.h"
#include "token_counter.h"
#include "queue.h"
#include "logger.h"
#include <yaml.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>

typedef struct provider_entry {
    const char* name;
    const provider_ops_t* ops;
    void* ctx;
    struct provider_entry* next;
} provider_entry_t;

struct llm_service {
    provider_entry_t* providers;
    cache_t* cache;
    cost_tracker_t* cost_tracker;
    token_counter_t* token_counter;
    request_queue_t* queue;
    pthread_t worker_thread;
    volatile int running;
    pthread_mutex_t lock;
};

/* 从 YAML 加载配置 */
static int load_config(const char* path, llm_service_t* svc) {
    FILE* f = fopen(path, "rb");
    if (!f) {
        AGENTOS_LOG_ERROR("service: cannot open config %s", path);
        return -1;
    }

    yaml_parser_t parser;
    yaml_event_t event;
    yaml_parser_initialize(&parser);
    yaml_parser_set_input_file(&parser, f);

    int in_providers = 0;
    char* current_provider = NULL;
    provider_config_t pcfg = {0};

    while (1) {
        if (!yaml_parser_parse(&parser, &event)) break;
        if (event.type == YAML_SCALAR_EVENT) {
            const char* val = (const char*)event.data.scalar.value;
            if (!in_providers && strcmp(val, "providers") == 0) {
                in_providers = 1;
            } else if (in_providers && strcmp(val, "name") == 0) {
                yaml_parser_parse(&parser, &event);
                current_provider = strdup((const char*)event.data.scalar.value);
            } else if (in_providers && current_provider && strcmp(val, "api_key") == 0) {
                yaml_parser_parse(&parser, &event);
                pcfg.api_key = strdup((const char*)event.data.scalar.value);
            } else if (in_providers && current_provider && strcmp(val, "api_base") == 0) {
                yaml_parser_parse(&parser, &event);
                pcfg.api_base = strdup((const char*)event.data.scalar.value);
            } else if (in_providers && current_provider && strcmp(val, "organization") == 0) {
                yaml_parser_parse(&parser, &event);
                pcfg.organization = strdup((const char*)event.data.scalar.value);
            } else if (in_providers && current_provider && strcmp(val, "timeout_sec") == 0) {
                yaml_parser_parse(&parser, &event);
                pcfg.timeout_sec = atof((const char*)event.data.scalar.value);
            } else if (in_providers && current_provider && strcmp(val, "max_retries") == 0) {
                yaml_parser_parse(&parser, &event);
                pcfg.max_retries = atoi((const char*)event.data.scalar.value);
            }
        } else if (event.type == YAML_MAPPING_END_EVENT) {
            if (in_providers && current_provider) {
                const provider_ops_t* ops = provider_get_ops(current_provider);
                if (ops) {
                    pcfg.name = current_provider;
                    void* ctx = ops->init(&pcfg);
                    if (ctx) {
                        provider_entry_t* e = (provider_entry_t*)malloc(sizeof(provider_entry_t));
                        if (e) {
                            e->name = strdup(current_provider);
                            e->ops = ops;
                            e->ctx = ctx;
                            e->next = svc->providers;
                            svc->providers = e;
                        }
                    } else {
                        AGENTOS_LOG_ERROR("service: failed to init provider %s", current_provider);
                    }
                } else {
                    AGENTOS_LOG_ERROR("service: unknown provider %s", current_provider);
                }
                free((void*)pcfg.api_key);
                free((void*)pcfg.api_base);
                free((void*)pcfg.organization);
                free(current_provider);
                current_provider = NULL;
                memset(&pcfg, 0, sizeof(pcfg));
            }
        }
        yaml_event_delete(&event);
        if (event.type == YAML_STREAM_END_EVENT) break;
    }
    yaml_parser_delete(&parser);
    fclose(f);
    return 0;
}

/* 工作线程：处理队列中的请求 */
static void* worker_thread_func(void* arg) {
    llm_service_t* svc = (llm_service_t*)arg;
    while (svc->running) {
        // 从队列中取出请求并处理（简化版，实际需更复杂调度）
        // 这里仅作占位，实际 llm_service_complete 是同步的，无需队列
        sleep(1);
    }
    return NULL;
}

llm_service_t* llm_service_create(const char* config_path) {
    llm_service_t* svc = (llm_service_t*)calloc(1, sizeof(llm_service_t));
    if (!svc) return NULL;

    pthread_mutex_init(&svc->lock, NULL);

    // 创建缓存
    svc->cache = cache_create(1000, 3600); // 1000条，TTL 1小时
    if (!svc->cache) {
        AGENTOS_LOG_ERROR("service: failed to create cache");
        goto fail;
    }

    // 创建成本跟踪器
    svc->cost_tracker = cost_tracker_create();
    if (!svc->cost_tracker) {
        AGENTOS_LOG_ERROR("service: failed to create cost tracker");
        goto fail;
    }

    // 创建 Token 计数器
    svc->token_counter = token_counter_create("cl100k_base");
    if (!svc->token_counter) {
        AGENTOS_LOG_ERROR("service: failed to create token counter");
        goto fail;
    }

    // 创建请求队列
    svc->queue = queue_create(1024);
    if (!svc->queue) {
        AGENTOS_LOG_ERROR("service: failed to create queue");
        goto fail;
    }

    // 加载配置
    if (config_path && load_config(config_path, svc) != 0) {
        AGENTOS_LOG_ERROR("service: failed to load config");
        goto fail;
    }

    // 启动工作线程（可选）
    svc->running = 1;
    if (pthread_create(&svc->worker_thread, NULL, worker_thread_func, svc) != 0) {
        AGENTOS_LOG_ERROR("service: failed to create worker thread");
        svc->running = 0;
        goto fail;
    }

    AGENTOS_LOG_INFO("service: initialized with %d providers", (int)svc->providers?1:0);
    return svc;

fail:
    if (svc->cache) cache_destroy(svc->cache);
    if (svc->cost_tracker) cost_tracker_destroy(svc->cost_tracker);
    if (svc->token_counter) token_counter_destroy(svc->token_counter);
    if (svc->queue) queue_destroy(svc->queue);
    pthread_mutex_destroy(&svc->lock);
    free(svc);
    return NULL;
}

void llm_service_destroy(llm_service_t* svc) {
    if (!svc) return;
    svc->running = 0;
    pthread_join(svc->worker_thread, NULL);
    pthread_mutex_lock(&svc->lock);
    provider_entry_t* p = svc->providers;
    while (p) {
        provider_entry_t* next = p->next;
        p->ops->destroy(p->ctx);
        free((void*)p->name);
        free(p);
        p = next;
    }
    cache_destroy(svc->cache);
    cost_tracker_destroy(svc->cost_tracker);
    token_counter_destroy(svc->token_counter);
    queue_destroy(svc->queue);
    pthread_mutex_unlock(&svc->lock);
    pthread_mutex_destroy(&svc->lock);
    free(svc);
}

int llm_service_complete(llm_service_t* svc,
                         const llm_request_config_t* config,
                         llm_response_t** out_response) {
    if (!svc || !config || !out_response) return -1;

    // 根据配置选择提供商（简化：取第一个支持该模型的）
    provider_entry_t* p = svc->providers;
    while (p) {
        // 这里可以加更复杂的路由逻辑，如根据模型名匹配
        // 简化为使用第一个
        break;
    }
    if (!p) {
        AGENTOS_LOG_ERROR("service: no provider available");
        return -1;
    }

    // 构建请求体
    char* request_body = p->ops->build_request(p->ctx, config);
    if (!request_body) {
        AGENTOS_LOG_ERROR("service: failed to build request");
        return -1;
    }

    // 确定 URL（应从 p->ctx 中获取）
    // 简化：使用固定 URL，实际应通过配置
    char url[512];
    snprintf(url, sizeof(url), "https://api.openai.com/v1/chat/completions"); // 示例

    // 执行 HTTP 请求
    http_buffer_t* resp = NULL;
    long http_code = 0;
    int ret = provider_http_post(url, "dummy-key", request_body, 30.0, &resp, &http_code);
    free(request_body);
    if (ret != 0) {
        AGENTOS_LOG_ERROR("service: http request failed");
        return -1;
    }

    if (http_code != 200) {
        char* err = p->ops->extract_error(p->ctx, resp->data);
        AGENTOS_LOG_ERROR("service: provider returned %ld: %s", http_code, err ? err : "unknown");
        free(err);
        provider_http_buffer_free(resp);
        return -1;
    }

    // 解析响应
    ret = p->ops->parse_response(p->ctx, resp->data, out_response);
    provider_http_buffer_free(resp);
    if (ret != 0) {
        AGENTOS_LOG_ERROR("service: failed to parse response");
        return -1;
    }

    // 更新成本跟踪
    llm_response_t* r = *out_response;
    cost_tracker_add(svc->cost_tracker, config->model, r->prompt_tokens, r->completion_tokens);

    return 0;
}

int llm_service_complete_stream(llm_service_t* svc,
                                const llm_request_config_t* config,
                                llm_stream_callback_t callback,
                                llm_response_t** out_response) {
    // 流式实现需要保持连接并逐步解析，较复杂，此处省略
    AGENTOS_LOG_ERROR("service: streaming not implemented yet");
    return -1;
}

void llm_response_free(llm_response_t* resp) {
    if (!resp) return;
    free(resp->id);
    free(resp->model);
    for (size_t i = 0; i < resp->choice_count; i++) {
        free(resp->choices[i].role);
        free(resp->choices[i].content);
    }
    free(resp->choices);
    free(resp->finish_reason);
    free(resp);
}

int llm_service_stats(llm_service_t* svc, char** out_json) {
    if (!svc || !out_json) return -1;
    // 生成统计 JSON
    cJSON* root = cJSON_CreateObject();
    cJSON_AddItemToObject(root, "cost", cost_tracker_export(svc->cost_tracker));
    char* json = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);
    if (!json) return -1;
    *out_json = json;
    return 0;
}