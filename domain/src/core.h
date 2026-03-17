/**
 * @file core.h
 * @brief Domain 核心内部定义
 */
#ifndef DOMAIN_CORE_H
#define DOMAIN_CORE_H

#include "domain.h"
#include "workbench/workbench.h"
#include "permission/permission.h"
#include "audit/audit.h"
#include "sanitizer/sanitizer.h"
#include <pthread.h>

struct domain_core {
    domain_config_t         config;
    workbench_manager_t*    wb_mgr;
    permission_engine_t*    perm_eng;
    audit_logger_t*         audit;
    sanitizer_t*            sanitizer;
    pthread_mutex_t         lock;
    volatile int            initialized;
};

#endif /* DOMAIN_CORE_H */