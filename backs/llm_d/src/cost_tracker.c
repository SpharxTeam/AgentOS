/**
 * @file cost_tracker.c
 * @brief 成本跟踪实现
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#include "cost_tracker.h"
#include <stdlib.h>
#include <string.h>
#include <pthread.h>

typedef struct model_cost {
    char* model;
    uint64_t prompt_tokens;
    uint64_t completion_tokens;
    double cost_usd;   // 累计美元成本
    struct model_cost* next;
} model_cost_t;

struct cost_tracker {
    model_cost_t* models;
    pthread_mutex_t lock;
};

cost_tracker_t* cost_tracker_create(void) {
    cost_tracker_t* ct = (cost_tracker_t*)calloc(1, sizeof(cost_tracker_t));
    if (!ct) return NULL;
    pthread_mutex_init(&ct->lock, NULL);
    return ct;
}

void cost_tracker_destroy(cost_tracker_t* ct) {
    if (!ct) return;
    pthread_mutex_lock(&ct->lock);
    model_cost_t* m = ct->models;
    while (m) {
        model_cost_t* next = m->next;
        free(m->model);
        free(m);
        m = next;
    }
    pthread_mutex_unlock(&ct->lock);
    pthread_mutex_destroy(&ct->lock);
    free(ct);
}

// 定价表（美元/千token）
static double get_price(const char* model, int is_output) {
    // 简单硬编码，实际应从配置文件加载
    if (strstr(model, "gpt-4")) {
        return is_output ? 0.06 : 0.03;
    } else if (strstr(model, "gpt-3.5")) {
        return is_output ? 0.002 : 0.0015;
    } else if (strstr(model, "claude-3-opus")) {
        return is_output ? 0.075 : 0.015;
    } else if (strstr(model, "deepseek")) {
        return is_output ? 0.002 : 0.001;
    } else {
        return is_output ? 0.002 : 0.001; // 默认
    }
}

void cost_tracker_add(cost_tracker_t* ct, const char* model,
                      uint32_t prompt_tokens, uint32_t completion_tokens) {
    if (!ct || !model) return;
    pthread_mutex_lock(&ct->lock);
    model_cost_t* m = ct->models;
    while (m) {
        if (strcmp(m->model, model) == 0) break;
        m = m->next;
    }
    if (!m) {
        m = (model_cost_t*)calloc(1, sizeof(model_cost_t));
        if (!m) {
            pthread_mutex_unlock(&ct->lock);
            return;
        }
        m->model = strdup(model);
        m->next = ct->models;
        ct->models = m;
    }
    m->prompt_tokens += prompt_tokens;
    m->completion_tokens += completion_tokens;
    double cost = (prompt_tokens / 1000.0) * get_price(model, 0) +
                  (completion_tokens / 1000.0) * get_price(model, 1);
    m->cost_usd += cost;
    pthread_mutex_unlock(&ct->lock);
}

cJSON* cost_tracker_export(cost_tracker_t* ct) {
    if (!ct) return NULL;
    pthread_mutex_lock(&ct->lock);
    cJSON* root = cJSON_CreateObject();
    cJSON* models_arr = cJSON_CreateArray();
    model_cost_t* m = ct->models;
    while (m) {
        cJSON* obj = cJSON_CreateObject();
        cJSON_AddStringToObject(obj, "model", m->model);
        cJSON_AddNumberToObject(obj, "prompt_tokens", m->prompt_tokens);
        cJSON_AddNumberToObject(obj, "completion_tokens", m->completion_tokens);
        cJSON_AddNumberToObject(obj, "cost_usd", m->cost_usd);
        cJSON_AddItemToArray(models_arr, obj);
        m = m->next;
    }
    cJSON_AddItemToObject(root, "models", models_arr);
    pthread_mutex_unlock(&ct->lock);
    return root;
}