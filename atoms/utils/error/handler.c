/**
 * @file handler.c
 * @brief 错误处理实现
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#include "error.h"
#include "../observability/include/logger.h"
#include <stdio.h>
#include <stdarg.h>

void agentos_error_handle(agentos_error_t err, const char* file, int line, const char* fmt, ...) {
    char buf[1024];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    AGENTOS_LOG_ERROR("Error %d (%s) at %s:%d: %s", err, agentos_error_str(err), file, line, buf);
}