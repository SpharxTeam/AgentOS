/**
 * @file token_counter.c
 * @brief Token 计数实现（基于 tiktoken）
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#include "token_counter.h"
#include "logger.h"
#include <stdlib.h>
#include <string.h>

struct token_counter {
    tiktoken_t* enc;
    char* encoding_name;
};

token_counter_t* token_counter_create(const char* encoding_name) {
    token_counter_t* tc = (token_counter_t*)calloc(1, sizeof(token_counter_t));
    if (!tc) return NULL;
    tc->enc = tiktoken_get_encoding(encoding_name);
    if (!tc->enc) {
        AGENTOS_LOG_ERROR("token_counter: failed to get encoding %s", encoding_name);
        free(tc);
        return NULL;
    }
    tc->encoding_name = strdup(encoding_name);
    return tc;
}

void token_counter_destroy(token_counter_t* tc) {
    if (!tc) return;
    tiktoken_free(tc->enc);
    free(tc->encoding_name);
    free(tc);
}

size_t token_counter_count(token_counter_t* tc, const char* text) {
    if (!tc || !text) return (size_t)-1;
    return tiktoken_count_tokens(tc->enc, text);
}

size_t token_counter_count_messages(token_counter_t* tc,
                                    const llm_message_t* messages,
                                    size_t count) {
    if (!tc || !messages) return 0;
    size_t total = 0;
    for (size_t i = 0; i < count; i++) {
        total += tiktoken_count_tokens(tc->enc, messages[i].content);
    }
    // 添加格式开销（每消息约4 token）
    total += count * 4;
    return total;
}