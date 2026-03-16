/**
 * @file timer.c
 * @brief 定时器管理
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#include "time.h"
#include "task.h"
#include "mem.h"
#include <stddef.h>

typedef struct timer_node {
    uint64_t id;
    uint32_t interval_ms;
    void (*callback)(void*);
    void* userdata;
    uint64_t next_expire;
    struct timer_node* next;
} timer_node_t;

static timer_node_t* timer_list = NULL;
static agentos_mutex_t* timer_lock = NULL;
static uint64_t next_timer_id = 1;

agentos_error_t agentos_time_timer_create(
    uint32_t interval_ms,
    void (*callback)(void* userdata),
    void* userdata,
    uint64_t* out_timer_id) {

    if (!callback) return AGENTOS_EINVAL;

    timer_node_t* node = (timer_node_t*)agentos_mem_alloc(sizeof(timer_node_t));
    if (!node) return AGENTOS_ENOMEM;

    node->id = next_timer_id++;
    node->interval_ms = interval_ms;
    node->callback = callback;
    node->userdata = userdata;
    node->next_expire = agentos_time_monotonic_ns() / 1000000 + interval_ms;

    agentos_mutex_lock(timer_lock);
    node->next = timer_list;
    timer_list = node;
    agentos_mutex_unlock(timer_lock);

    if (out_timer_id) *out_timer_id = node->id;
    return AGENTOS_SUCCESS;
}

void agentos_time_timer_cancel(uint64_t timer_id) {
    agentos_mutex_lock(timer_lock);
    timer_node_t** p = &timer_list;
    while (*p) {
        if ((*p)->id == timer_id) {
            timer_node_t* tmp = *p;
            *p = tmp->next;
            agentos_mem_free(tmp);
            break;
        }
        p = &(*p)->next;
    }
    agentos_mutex_unlock(timer_lock);
}

void agentos_time_timer_process(void) {
    uint64_t now = agentos_time_monotonic_ns() / 1000000;
    agentos_mutex_lock(timer_lock);
    timer_node_t* node = timer_list;
    timer_node_t* prev = NULL;
    while (node) {
        if (node->next_expire <= now) {
            // 触发回调
            node->callback(node->userdata);
            if (node->interval_ms > 0) {
                // 周期性定时器，重置
                node->next_expire = now + node->interval_ms;
                prev = node;
                node = node->next;
            } else {
                // 一次性定时器，删除
                timer_node_t* to_delete = node;
                if (prev) {
                    prev->next = node->next;
                } else {
                    timer_list = node->next;
                }
                node = node->next;
                agentos_mem_free(to_delete);
            }
        } else {
            prev = node;
            node = node->next;
        }
    }
    agentos_mutex_unlock(timer_lock);
}