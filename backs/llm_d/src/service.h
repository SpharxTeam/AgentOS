/**
 * @file service.h
 * @brief LLM 服务内部结构定义
 */

#ifndef AGENTOS_LLM_SERVICE_INTERNAL_H
#define AGENTOS_LLM_SERVICE_INTERNAL_H

#include "llm_service.h"
#include "providers/provider.h"
#include "cache.h"
#include "cost_tracker.h"
#include "token_counter.h"
#include "queue.h"
#include "config.h"
#include <pthread.h>

struct llm_service {
    provider_t*         primary;
    provider_t*         fallback;
    cache_t*            cache;
    cost_tracker_t*     cost;
    token_counter_t*    token_counter;
    request_queue_t*    queue;
    pthread_t*          workers;
    size_t              worker_count;
    volatile int        running;
    pthread_mutex_t     lock;
    llm_service_config  cfg;
};

#endif /* AGENTOS_LLM_SERVICE_INTERNAL_H */