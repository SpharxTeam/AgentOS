/**
 * @file cache.h
 * @brief LLM 响应缓存（LRU）
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#ifndef LLM_CACHE_H
#define LLM_CACHE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct cache cache_t;

/**
 * @brief 创建缓存
 * @param capacity 最大条目数
 * @param ttl_sec 生存时间（秒），0表示永久
 * @return 缓存句柄，失败返回 NULL
 */
cache_t* cache_create(size_t capacity, uint32_t ttl_sec);

/**
 * @brief 销毁缓存
 */
void cache_destroy(cache_t* cache);

/**
 * @brief 获取缓存条目
 * @param cache 缓存
 * @param key 键（请求的哈希）
 * @param out_value 输出值（需调用者 free）
 * @return 1 命中，0 未命中，-1 错误
 */
int cache_get(cache_t* cache, const char* key, char** out_value);

/**
 * @brief 存入缓存
 * @param cache 缓存
 * @param key 键
 * @param value 值（内部会复制）
 */
void cache_put(cache_t* cache, const char* key, const char* value);

/**
 * @brief 清空缓存
 */
void cache_clear(cache_t* cache);

#ifdef __cplusplus
}
#endif

#endif /* LLM_CACHE_H */