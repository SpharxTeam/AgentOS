/**
 * @file cache.c
 * @brief LRU 缓存实现
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#include "cache.h"
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>

typedef struct cache_entry {
    char* key;
    char* value;
    time_t timestamp;
    struct cache_entry* prev;
    struct cache_entry* next;
} cache_entry_t;

struct cache {
    cache_entry_t* head;
    cache_entry_t* tail;
    size_t capacity;
    size_t size;
    uint32_t ttl_sec;
    pthread_mutex_t lock;
};

static void free_entry(cache_entry_t* e) {
    free(e->key);
    free(e->value);
    free(e);
}

static void move_to_head(cache_t* cache, cache_entry_t* e) {
    if (e == cache->head) return;
    // 从链表中移除
    if (e->prev) e->prev->next = e->next;
    if (e->next) e->next->prev = e->prev;
    if (cache->tail == e) cache->tail = e->prev;
    // 插入头部
    e->next = cache->head;
    e->prev = NULL;
    if (cache->head) cache->head->prev = e;
    cache->head = e;
    if (!cache->tail) cache->tail = e;
}

static void evict_lru(cache_t* cache) {
    if (!cache->tail) return;
    cache_entry_t* tail = cache->tail;
    cache->tail = tail->prev;
    if (cache->tail) cache->tail->next = NULL;
    free_entry(tail);
    cache->size--;
}

cache_t* cache_create(size_t capacity, uint32_t ttl_sec) {
    cache_t* cache = (cache_t*)calloc(1, sizeof(cache_t));
    if (!cache) return NULL;
    cache->capacity = capacity;
    cache->ttl_sec = ttl_sec;
    pthread_mutex_init(&cache->lock, NULL);
    return cache;
}

void cache_destroy(cache_t* cache) {
    if (!cache) return;
    pthread_mutex_lock(&cache->lock);
    cache_entry_t* e = cache->head;
    while (e) {
        cache_entry_t* next = e->next;
        free_entry(e);
        e = next;
    }
    pthread_mutex_unlock(&cache->lock);
    pthread_mutex_destroy(&cache->lock);
    free(cache);
}

int cache_get(cache_t* cache, const char* key, char** out_value) {
    if (!cache || !key || !out_value) return -1;
    pthread_mutex_lock(&cache->lock);
    cache_entry_t* e = cache->head;
    time_t now = time(NULL);
    int found = 0;
    while (e) {
        if (strcmp(e->key, key) == 0) {
            if (cache->ttl_sec == 0 || (now - e->timestamp) <= (time_t)cache->ttl_sec) {
                *out_value = strdup(e->value);
                found = 1;
                move_to_head(cache, e);
            } else {
                // 过期，移除
                if (e->prev) e->prev->next = e->next;
                if (e->next) e->next->prev = e->prev;
                if (cache->head == e) cache->head = e->next;
                if (cache->tail == e) cache->tail = e->prev;
                free_entry(e);
                cache->size--;
            }
            break;
        }
        e = e->next;
    }
    pthread_mutex_unlock(&cache->lock);
    return found ? 1 : 0;
}

void cache_put(cache_t* cache, const char* key, const char* value) {
    if (!cache || !key || !value) return;
    pthread_mutex_lock(&cache->lock);

    // 如果已存在，先删除
    cache_entry_t** p = &cache->head;
    while (*p) {
        if (strcmp((*p)->key, key) == 0) {
            cache_entry_t* victim = *p;
            *p = victim->next;
            if (victim->next) victim->next->prev = victim->prev;
            if (cache->tail == victim) cache->tail = victim->prev;
            free_entry(victim);
            cache->size--;
            break;
        }
        p = &(*p)->next;
    }

    cache_entry_t* e = (cache_entry_t*)malloc(sizeof(cache_entry_t));
    if (!e) {
        pthread_mutex_unlock(&cache->lock);
        return;
    }
    e->key = strdup(key);
    e->value = strdup(value);
    e->timestamp = time(NULL);
    e->prev = NULL;
    e->next = cache->head;
    if (cache->head) cache->head->prev = e;
    cache->head = e;
    if (!cache->tail) cache->tail = e;
    cache->size++;

    while (cache->capacity > 0 && cache->size > cache->capacity) {
        evict_lru(cache);
    }
    pthread_mutex_unlock(&cache->lock);
}

void cache_clear(cache_t* cache) {
    if (!cache) return;
    pthread_mutex_lock(&cache->lock);
    cache_entry_t* e = cache->head;
    while (e) {
        cache_entry_t* next = e->next;
        free_entry(e);
        e = next;
    }
    cache->head = cache->tail = NULL;
    cache->size = 0;
    pthread_mutex_unlock(&cache->lock);
}