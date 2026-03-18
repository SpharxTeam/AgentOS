/**
 * @file logger.c
 * @brief 日志实现
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#include "logger.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdarg.h>
#include <pthread.h>

static pthread_mutex_t log_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_key_t trace_key;
static pthread_once_t trace_key_once = PTHREAD_ONCE_INIT;

static void make_key(void) {
    pthread_key_create(&trace_key, free);
}

const char* agentos_log_set_trace_id(const char* trace_id) {
    pthread_once(&trace_key_once, make_key);
    char* old = (char*)pthread_getspecific(trace_key);
    if (old) free(old);
    char* new;
    if (trace_id) {
        new = strdup(trace_id);
    } else {
        char buf[32];
        snprintf(buf, sizeof(buf), "%lx", (unsigned long)time(NULL) ^ (unsigned long)pthread_self());
        new = strdup(buf);
    }
    pthread_setspecific(trace_key, new);
    return new;
}

const char* agentos_log_get_trace_id(void) {
    pthread_once(&trace_key_once, make_key);
    return (const char*)pthread_getspecific(trace_key);
}

static const char* level_str(int level) {
    switch (level) {
        case AGENTOS_LOG_LEVEL_ERROR: return "ERROR";
        case AGENTOS_LOG_LEVEL_WARN:  return "WARN";
        case AGENTOS_LOG_LEVEL_INFO:  return "INFO";
        case AGENTOS_LOG_LEVEL_DEBUG: return "DEBUG";
        default: return "UNKNOWN";
    }
}

void agentos_log_write(int level, const char* file, int line, const char* fmt, ...) {
    if (level > AGENTOS_LOG_LEVEL) return;
    time_t now = time(NULL);
    struct tm* tm_info = localtime(&now);
    char time_buf[32];
    strftime(time_buf, sizeof(time_buf), "%Y-%m-%d %H:%M:%S", tm_info);

    pthread_mutex_lock(&log_mutex);
    fprintf(stderr, "[%s] %s %s:%d ", time_buf, level_str(level), file, line);
    const char* trace = agentos_log_get_trace_id();
    if (trace) fprintf(stderr, "[%s] ", trace);
    va_list args;
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);
    fprintf(stderr, "\n");
    fflush(stderr);
    pthread_mutex_unlock(&log_mutex);
}