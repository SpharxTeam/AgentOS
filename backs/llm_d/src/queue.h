/**
 * @file queue.h
 * @brief 请求队列（线程安全）
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#ifndef LLM_QUEUE_H
#define LLM_QUEUE_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct request_queue request_queue_t;

/**
 * @brief 创建队列
 * @param capacity 最大容量
 * @return 队列句柄，失败返回 NULL
 */
request_queue_t* queue_create(size_t capacity);

/**
 * @brief 销毁队列
 */
void queue_destroy(request_queue_t* q);

/**
 * @brief 入队
 * @param q 队列
 * @param data 数据（内部会复制）
 * @param timeout_ms 超时（毫秒），-1无限
 * @return 0 成功，-1 失败
 */
int queue_push(request_queue_t* q, const char* data, int timeout_ms);

/**
 * @brief 出队
 * @param q 队列
 * @param out_data 输出数据（需调用者 free）
 * @param timeout_ms 超时
 * @return 0 成功，-1 失败
 */
int queue_pop(request_queue_t* q, char** out_data, int timeout_ms);

#ifdef __cplusplus
}
#endif

#endif /* LLM_QUEUE_H */