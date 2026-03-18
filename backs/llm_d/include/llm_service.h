/**
 * @file llm_service.h
 * @brief LLM 服务对外接口
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 *
 * @design
 * - 不透明指针隐藏实现细节
 * - 所有函数返回统一错误码（0成功，-1失败，errno辅助）
 * - 资源所有权明确：调用者负责释放 out_response 和 out_json
 */

#ifndef AGENTOS_LLM_SERVICE_H
#define AGENTOS_LLM_SERVICE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ---------- 前向声明 ---------- */
typedef struct llm_service llm_service_t;

/* ---------- 消息结构 ---------- */
typedef struct llm_message {
    const char* role;     /**< 角色: "system", "user", "assistant", 外部传入，不释放 */
    const char* content;  /**< 内容，外部传入，不释放 */
} llm_message_t;

/* ---------- 请求配置 ---------- */
typedef struct llm_request_config {
    const char* model;                    /**< 模型名称，外部传入 */
    const llm_message_t* messages;         /**< 消息数组，外部传入 */
    size_t message_count;                  /**< 消息数量 */
    float temperature;                     /**< 温度 (0.0 - 2.0) */
    float top_p;                           /**< Top P (0.0 - 1.0) */
    int max_tokens;                        /**< 最大输出token数，0表示不限制 */
    int stream;                            /**< 是否流式输出（0/1） */
    const char** stop;                     /**< 停止序列数组，外部传入 */
    size_t stop_count;                     /**< 停止序列数量 */
    double presence_penalty;                /**< 存在惩罚 (-2.0 - 2.0) */
    double frequency_penalty;               /**< 频率惩罚 (-2.0 - 2.0) */
    void* user_data;                        /**< 用户数据（用于回调） */
} llm_request_config_t;

/* ---------- 响应结构 ---------- */
typedef struct llm_response {
    char* id;                /**< 响应ID，内部分配，需释放 */
    char* model;             /**< 使用的模型，内部分配，需释放 */
    llm_message_t* choices;  /**< 生成的回复数组，内部分配，需释放 */
    size_t choice_count;     /**< 回复数量 */
    uint64_t created;        /**< 创建时间戳（Unix秒） */
    uint32_t prompt_tokens;  /**< 输入token数 */
    uint32_t completion_tokens; /**< 输出token数 */
    uint32_t total_tokens;   /**< 总token数 */
    char* finish_reason;     /**< 结束原因，内部分配，需释放 */
} llm_response_t;

/* ---------- 流式回调 ---------- */
typedef void (*llm_stream_callback_t)(const char* chunk, void* user_data);

/* ---------- 生命周期 ---------- */

/**
 * @brief 创建 LLM 服务实例
 * @param config_path 配置文件路径（YAML格式），必须非空
 * @return 服务句柄，失败返回 NULL 并设置 errno
 */
llm_service_t* llm_service_create(const char* config_path);

/**
 * @brief 销毁 LLM 服务
 * @param svc 服务句柄，允许 NULL
 */
void llm_service_destroy(llm_service_t* svc);

/* ---------- 同步请求 ---------- */

/**
 * @brief 发送 LLM 请求（非流式）
 * @param svc 服务句柄
 * @param config 请求配置，所有指针指向外部数据，函数内部不修改
 * @param out_response 输出响应，成功时指向新分配的响应，需调用 llm_response_free 释放
 * @return 0 成功，-1 失败（errno 指示具体错误）
 */
int llm_service_complete(llm_service_t* svc,
                         const llm_request_config_t* config,
                         llm_response_t** out_response);

/* ---------- 流式请求 ---------- */

/**
 * @brief 发送流式 LLM 请求
 * @param svc 服务句柄
 * @param config 请求配置
 * @param callback 流式回调函数，每收到一个内容块调用一次
 * @param out_response 可选，如果非 NULL，成功时填充最终完整响应（需释放），可为 NULL
 * @return 0 成功，-1 失败
 */
int llm_service_complete_stream(llm_service_t* svc,
                                const llm_request_config_t* config,
                                llm_stream_callback_t callback,
                                llm_response_t** out_response);

/* ---------- 资源释放 ---------- */

/**
 * @brief 释放响应结构
 * @param resp 响应指针，允许 NULL
 */
void llm_response_free(llm_response_t* resp);

/* ---------- 统计信息 ---------- */

/**
 * @brief 获取服务统计信息（JSON格式）
 * @param svc 服务句柄
 * @param out_json 输出JSON字符串，需调用 free 释放
 * @return 0 成功，-1 失败
 */
int llm_service_stats(llm_service_t* svc, char** out_json);

#ifdef __cplusplus
}
#endif

#endif /* AGENTOS_LLM_SERVICE_H */