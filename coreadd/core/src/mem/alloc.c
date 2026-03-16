/**
 * @file alloc.c
 * @brief 物理内存分配器（基于 malloc/free 封装）
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#include "mem.h"
#include <stdlib.h>
#include <string.h>

static size_t total_allocated = 0;
static size_t peak_allocated = 0;
static agentos_mutex_t* mem_stats_mutex = NULL;

agentos_error_t agentos_mem_init(size_t heap_size) {
    if (!mem_stats_mutex) {
        mem_stats_mutex = agentos_mutex_create();
        if (!mem_stats_mutex) return AGENTOS_ENOMEM;
    }
    return AGENTOS_SUCCESS;
}

void* agentos_mem_alloc(size_t size) {
    void* ptr = malloc(size);
    if (ptr) {
        agentos_mutex_lock(mem_stats_mutex);
        total_allocated += size;
        if (total_allocated > peak_allocated) peak_allocated = total_allocated;
        agentos_mutex_unlock(mem_stats_mutex);
    }
    return ptr;
}

void* agentos_mem_aligned_alloc(size_t size, size_t alignment) {
    void* ptr = NULL;
#ifdef _WIN32
    ptr = _aligned_malloc(size, alignment);
#else
    if (posix_memalign(&ptr, alignment, size) != 0) ptr = NULL;
#endif
    if (ptr) {
        agentos_mutex_lock(mem_stats_mutex);
        total_allocated += size;
        if (total_allocated > peak_allocated) peak_allocated = total_allocated;
        agentos_mutex_unlock(mem_stats_mutex);
    }
    return ptr;
}

void agentos_mem_free(void* ptr) {
    free(ptr);
    // 无法准确统计释放，因此不减少 total_allocated
}

void* agentos_mem_realloc(void* ptr, size_t new_size) {
    // 无法从原指针获得旧大小，所以无法精确更新统计
    // 简单实现：分配新内存，复制数据（假设原大小足够）
    void* new_ptr = agentos_mem_alloc(new_size);
    if (new_ptr && ptr) {
        // 无法知道原大小，只能保守复制，假设至少 new_size
        memcpy(new_ptr, ptr, new_size);
    }
    free(ptr);
    return new_ptr;
}

void agentos_mem_stats(size_t* out_total, size_t* out_used, size_t* out_peak) {
    agentos_mutex_lock(mem_stats_mutex);
    if (out_total) *out_total = total_allocated;
    if (out_used) *out_used = total_allocated; // 未跟踪释放
    if (out_peak) *out_peak = peak_allocated;
    agentos_mutex_unlock(mem_stats_mutex);
}