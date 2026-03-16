/**
 * @file task.h
 * @brief 任务调度接口（包含线程、锁、条件变量）
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#ifndef AGENTOS_TASK_H
#define AGENTOS_TASK_H

#include <stdint.h>
#include <stddef.h>
#include "error.h"

#ifdef __cplusplus
extern "C" {
#endif

/** 任务 ID 类型 */
typedef uint64_t agentos_task_id_t;

/** 互斥锁 */
typedef struct agentos_mutex agentos_mutex_t;

/** 条件变量 */
typedef struct agentos_cond agentos_cond_t;

/** 线程句柄 */
typedef struct agentos_thread agentos_thread_t;

/**
 * @brief 创建互斥锁
 * @return 锁句柄，失败返回 NULL
 */
agentos_mutex_t* agentos_mutex_create(void);

/**
 * @brief 销毁互斥锁
 * @param mutex 锁句柄
 */
void agentos_mutex_destroy(agentos_mutex_t* mutex);

/**
 * @brief 加锁
 * @param mutex 锁句柄
 */
void agentos_mutex_lock(agentos_mutex_t* mutex);

/**
 * @brief 尝试加锁
 * @param mutex 锁句柄
 * @return 0成功，非0失败
 */
int agentos_mutex_trylock(agentos_mutex_t* mutex);

/**
 * @brief 解锁
 * @param mutex 锁句柄
 */
void agentos_mutex_unlock(agentos_mutex_t* mutex);

/**
 * @brief 创建条件变量
 * @return 条件变量句柄，失败返回 NULL
 */
agentos_cond_t* agentos_cond_create(void);

/**
 * @brief 销毁条件变量
 * @param cond 句柄
 */
void agentos_cond_destroy(agentos_cond_t* cond);

/**
 * @brief 等待条件变量
 * @param cond 条件变量
 * @param mutex 已锁定的互斥锁
 * @param timeout_ms 超时毫秒（0表示无限等待）
 * @return AGENTOS_SUCCESS 或 AGENTOS_ETIMEDOUT
 */
agentos_error_t agentos_cond_wait(
    agentos_cond_t* cond,
    agentos_mutex_t* mutex,
    uint32_t timeout_ms);

/**
 * @brief 唤醒一个等待线程
 * @param cond 条件变量
 */
void agentos_cond_signal(agentos_cond_t* cond);

/**
 * @brief 唤醒所有等待线程
 * @param cond 条件变量
 */
void agentos_cond_broadcast(agentos_cond_t* cond);

/**
 * @brief 创建线程
 * @param thread 输出线程句柄
 * @param func 线程函数
 * @param arg 参数
 * @return AGENTOS_SUCCESS 或错误码
 */
agentos_error_t agentos_thread_create(
    agentos_thread_t* thread,
    void (*func)(void*),
    void* arg);

/**
 * @brief 等待线程结束
 * @param thread 线程句柄
 * @param retval 输出返回值（可为NULL）
 * @return AGENTOS_SUCCESS
 */
agentos_error_t agentos_thread_join(agentos_thread_t thread, void** retval);

/**
 * @brief 获取当前任务ID
 * @return 当前任务ID
 */
agentos_task_id_t agentos_task_self(void);

/**
 * @brief 任务睡眠（毫秒）
 * @param ms 毫秒
 */
void agentos_task_sleep(uint32_t ms);

#ifdef __cplusplus
}
#endif

#endif /* AGENTOS_TASK_H */