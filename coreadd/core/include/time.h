/**
 * @file time.h
 * @brief 时间服务接口
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#ifndef AGENTOS_TIME_H
#define AGENTOS_TIME_H

#include <stdint.h>
#include "error.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 获取系统启动以来的单调时间（纳秒）
 * @return 单调时间
 */
uint64_t agentos_time_monotonic_ns(void);

#ifdef __cplusplus
}
#endif

#endif /* AGENTOS_TIME_H */