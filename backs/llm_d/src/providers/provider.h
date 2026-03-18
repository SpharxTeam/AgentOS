/**
 * @file provider.h
 * @brief 提供商适配器接口，插件式架构
 * @copyright (c) 2026 SPHARX. All Rights Reserved.
 *
 * @design
 * - 每个提供商实现一个虚表（provider_ops_t）
 * - 服务层通过该接口调用，实现多态
 * - 所有提供商共享通用HTTP工具和JSON工具
 */

#ifndef LLM_PROVIDER_H
#define LLM_PROVIDER_H

#include "llm_service.h"
#include <curl/curl.h>
#include <cjson/cJSON.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ---------- 配置结构 ---------- */
typedef struct provider_config {
    const char* name;           /**< 提供商名称（如 "openai"） */
    const char* api_key;        /**< API密钥 */
    const char* api_base;       /**< API基础URL（可选） */
    const char* organization;   /**< 组织ID（如OpenAI需要） */
    double timeout_sec;         /**< 请求超时（秒） */
    int max_retries;            /**< 最大重试次数 */
    char** models;              /**< 支持的模型列表（以NULL结尾） */
    size_t model_count;         /**< 模型数量 */
} provider_config_t;

/* ---------- HTTP响应缓冲区（内部使用） ---------- */
typedef struct http_buffer {
    char* data;    /**< 动态分配的数据，以'\0'结尾 */
    size_t size;   /**< 数据长度（不含结尾\0） */
} http_buffer_t;

/* ---------- 提供商操作表 ---------- */
typedef struct provider_ops {
    /**
     * @brief 初始化提供商
     * @param config 配置（只读）
     * @return 提供商上下文，失败返回 NULL
     */
    void* (*init)(const provider_config_t* config);

    /**
     * @brief 销毁提供商上下文
     */
    void (*destroy)(void* ctx);

    /**
     * @brief 同步完成请求
     */
    int (*complete)(void* ctx,
                    const llm_request_config_t* config,
                    llm_response_t** out_response);

    /**
     * @brief 流式完成请求
     */
    int (*complete_stream)(void* ctx,
                           const llm_request_config_t* config,
                           llm_stream_callback_t callback,
                           llm_response_t** out_response);
} provider_ops_t;

/* ---------- 通用工具函数（供适配器使用） ---------- */

/**
 * @brief 执行 HTTP POST 请求（带重试）
 * @param url 完整URL
 * @param headers 额外的HTTP头（内部会自动添加 Content-Type）
 * @param body 请求体
 * @param timeout_sec 超时（秒）
 * @param max_retries 最大重试次数
 * @param out_response 输出缓冲区（成功时分配，需调用 provider_http_buffer_free）
 * @param out_http_code 输出HTTP状态码
 * @return 0 成功，-1 失败（所有重试后仍失败）
 */
int provider_http_post(const char* url,
                       struct curl_slist* headers,
                       const char* body,
                       double timeout_sec,
                       int max_retries,
                       http_buffer_t** out_response,
                       long* out_http_code);

/**
 * @brief 释放 HTTP 缓冲区
 */
void provider_http_buffer_free(http_buffer_t* buf);

/**
 * @brief 构建 OpenAI 兼容的请求体（供 openai, deepseek, local 复用）
 * @param config 请求配置
 * @return JSON 字符串，需 free
 */
char* provider_build_openai_request(const llm_request_config_t* config);

/**
 * @brief 解析 OpenAI 兼容的响应（供 openai, deepseek, local 复用）
 * @param body 响应体
 * @param out_response 输出响应
 * @return 0 成功，-1 失败
 */
int provider_parse_openai_response(const char* body, llm_response_t** out_response);

/**
 * @brief 提取 OpenAI 错误信息（用于错误日志）
 * @param body 错误响应体
 * @return 错误描述字符串，需 free，若无则返回 NULL
 */
char* provider_extract_openai_error(const char* body);

/* ---------- 提供商注册表 ---------- */

/**
 * @brief 注册所有内置提供商（初始化时调用）
 */
void provider_register_all(void);

/**
 * @brief 根据名称获取操作表
 */
const provider_ops_t* provider_get_ops(const char* name);

#ifdef __cplusplus
}
#endif

#endif /* LLM_PROVIDER_H */