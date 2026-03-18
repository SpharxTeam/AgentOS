/**
 * @file token_counter.h
 * @brief Token 计数器（基于 tiktoken）
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#ifndef LLM_TOKEN_COUNTER_H
#define LLM_TOKEN_COUNTER_H

#include <stddef.h>
#include <tiktoken.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct token_counter token_counter_t;

/**
 * @brief 创建 Token 计数器
 * @param encoding_name 编码名称（如 "cl100k_base"）
 * @return 句柄，失败返回 NULL
 */
token_counter_t* token_counter_create(const char* encoding_name);

/**
 * @brief 销毁计数器
 */
void token_counter_destroy(token_counter_t* tc);

/**
 * @brief 计算文本的 Token 数量
 * @param tc 计数器
 * @param text 文本
 * @return Token 数量，失败返回 (size_t)-1
 */
size_t token_counter_count(token_counter_t* tc, const char* text);

/**
 * @brief 计算消息列表的 Token 数量（适用于 Chat 格式）
 * @param tc 计数器
 * @param messages 消息数组
 * @param count 消息数量
 * @return Token 总数
 */
size_t token_counter_count_messages(token_counter_t* tc,
                                    const llm_message_t* messages,
                                    size_t count);

#ifdef __cplusplus
}
#endif

#endif /* LLM_TOKEN_COUNTER_H */