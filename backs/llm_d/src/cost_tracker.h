/**
 * @file cost_tracker.h
 * @brief 成本跟踪器
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#ifndef LLM_COST_TRACKER_H
#define LLM_COST_TRACKER_H

#include <stddef.h>
#include <stdint.h>
#include <cjson/cJSON.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct cost_tracker cost_tracker_t;

/**
 * @brief 创建成本跟踪器
 * @return 句柄，失败返回 NULL
 */
cost_tracker_t* cost_tracker_create(void);

/**
 * @brief 销毁跟踪器
 */
void cost_tracker_destroy(cost_tracker_t* ct);

/**
 * @brief 添加一次调用的成本
 * @param ct 跟踪器
 * @param model 模型名称
 * @param prompt_tokens 输入token数
 * @param completion_tokens 输出token数
 */
void cost_tracker_add(cost_tracker_t* ct, const char* model,
                      uint32_t prompt_tokens, uint32_t completion_tokens);

/**
 * @brief 导出成本统计为 JSON 对象（调用者需释放）
 */
cJSON* cost_tracker_export(cost_tracker_t* ct);

#ifdef __cplusplus
}
#endif

#endif /* LLM_COST_TRACKER_H */