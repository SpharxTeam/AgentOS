/**
 * @file hierarchical.c
 * @brief 分层规划策略：将复杂任务分解为层次化子任务
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#include "cognition.h"
#include "llm_client.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define MAX_SUBTASKS 16
#define MAX_DEPTH 5

/**
 * @brief 分层规划私有数据
 */
typedef struct hierarchical_data {
    agentos_llm_service_t* llm;      /**< LLM服务客户端 */
    int max_depth;                    /**< 最大分解深度 */
    agentos_mutex_t* lock;
} hierarchical_data_t;

static void hierarchical_destroy(agentos_plan_strategy_t* strategy) {
    if (!strategy) return;
    hierarchical_data_t* data = (hierarchical_data_t*)strategy->data;
    if (data) {
        if (data->lock) agentos_mutex_destroy(data->lock);
        free(data);
    }
    free(strategy);
}

/**
 * @brief 调用LLM生成子任务列表（JSON格式）
 */
static agentos_error_t generate_subtasks(
    agentos_llm_service_t* llm,
    const char* goal,
    char*** out_subtasks,
    int* out_count) {

    // 构造提示词，要求输出JSON数组
    char prompt[4096];
    snprintf(prompt, sizeof(prompt),
        "Decompose the following goal into a list of subtasks. "
        "Output a JSON array of strings, each subtask. Goal: %s",
        goal);

    agentos_llm_request_t req;
    memset(&req, 0, sizeof(req));
    req.model = "gpt-4"; // 可使用默认模型
    req.prompt = prompt;
    req.temperature = 0.5;
    req.max_tokens = 1024;

    agentos_llm_response_t* resp = NULL;
    agentos_error_t err = agentos_llm_complete(llm, &req, &resp);
    if (err != AGENTOS_SUCCESS) return err;

    // 简单解析JSON（实际应使用JSON库）
    // 这里假设返回格式如 ["subtask1", "subtask2"]
    char* text = resp->text;
    char** subtasks = NULL;
    int count = 0;

    // 非常简陋的解析，仅用于示例
    char* p = text;
    while (*p) {
        if (*p == '"') {
            p++;
            char* start = p;
            while (*p && *p != '"') p++;
            if (*p == '"') {
                size_t len = p - start;
                char* subtask = (char*)malloc(len + 1);
                if (!subtask) {
                    agentos_llm_response_free(resp);
                    return AGENTOS_ENOMEM;
                }
                strncpy(subtask, start, len);
                subtask[len] = '\0';
                subtasks = realloc(subtasks, sizeof(char*) * (count + 1));
                if (!subtasks) {
                    free(subtask);
                    agentos_llm_response_free(resp);
                    return AGENTOS_ENOMEM;
                }
                subtasks[count++] = subtask;
            }
        }
        p++;
    }

    agentos_llm_response_free(resp);
    *out_subtasks = subtasks;
    *out_count = count;
    return AGENTOS_SUCCESS;
}

/**
 * @brief 递归构建任务DAG
 */
static agentos_error_t build_hierarchical_plan(
    agentos_llm_service_t* llm,
    const char* goal,
    int depth,
    int max_depth,
    agentos_task_plan_t* plan) {

    if (depth >= max_depth) {
        // 达到最大深度，将当前目标作为一个任务节点
        agentos_task_node_t* node = (agentos_task_node_t*)calloc(1, sizeof(agentos_task_node_t));
        if (!node) return AGENTOS_ENOMEM;

        node->task_id = strdup(goal); // 简化：用goal作为ID（实际应生成唯一ID）
        node->agent_role = strdup("default"); // 需要更智能的角色分配
        node->depends_on = NULL;
        node->depends_count = 0;
        node->timeout_ms = 30000;
        node->priority = 128;
        node->input = NULL; // 可扩展

        // 添加到计划
        plan->nodes = realloc(plan->nodes, sizeof(agentos_task_node_t*) * (plan->node_count + 1));
        if (!plan->nodes) {
            free(node->task_id);
            free(node->agent_role);
            free(node);
            return AGENTOS_ENOMEM;
        }
        plan->nodes[plan->node_count++] = node;
        return AGENTOS_SUCCESS;
    }

    // 生成子任务
    char** subtasks = NULL;
    int subtask_count = 0;
    agentos_error_t err = generate_subtasks(llm, goal, &subtasks, &subtask_count);
    if (err != AGENTOS_SUCCESS) return err;

    if (subtask_count == 0) {
        // 没有子任务，直接作为叶子
        err = build_hierarchical_plan(llm, goal, max_depth, max_depth, plan);
    } else {
        // 对每个子任务递归构建
        for (int i = 0; i < subtask_count; i++) {
            err = build_hierarchical_plan(llm, subtasks[i], depth + 1, max_depth, plan);
            if (err != AGENTOS_SUCCESS) {
                for (int j = 0; j < subtask_count; j++) free(subtasks[j]);
                free(subtasks);
                return err;
            }
            free(subtasks[i]);
        }
        free(subtasks);
    }
    return AGENTOS_SUCCESS;
}

/**
 * @brief 分层规划函数
 */
static agentos_error_t hierarchical_plan(
    const agentos_intent_t* intent,
    void* context,
    agentos_task_plan_t** out_plan) {

    hierarchical_data_t* data = (hierarchical_data_t*)context;
    if (!data || !intent || !out_plan) return AGENTOS_EINVAL;

    agentos_task_plan_t* plan = (agentos_task_plan_t*)calloc(1, sizeof(agentos_task_plan_t));
    if (!plan) return AGENTOS_ENOMEM;

    // 生成计划ID
    plan->plan_id = strdup("hierarchical_plan_1"); // 实际应生成唯一ID
    plan->nodes = NULL;
    plan->node_count = 0;
    plan->entry_points = NULL;
    plan->entry_count = 0;

    agentos_error_t err = build_hierarchical_plan(
        data->llm, intent->goal, 0, data->max_depth, plan);

    if (err != AGENTOS_SUCCESS) {
        // 清理
        for (size_t i = 0; i < plan->node_count; i++) {
            free(plan->nodes[i]->task_id);
            free(plan->nodes[i]->agent_role);
            free(plan->nodes[i]);
        }
        free(plan->nodes);
        free(plan->plan_id);
        free(plan);
        return err;
    }

    // 确定入口点（没有依赖的任务）
    plan->entry_points = (char**)malloc(sizeof(char*));
    if (plan->entry_points) {
        // 简化：假设所有节点都无依赖
        plan->entry_count = plan->node_count;
        for (size_t i = 0; i < plan->node_count; i++) {
            plan->entry_points[i] = plan->nodes[i]->task_id;
        }
    }

    *out_plan = plan;
    return AGENTOS_SUCCESS;
}

/**
 * @brief 创建分层规划策略
 */
agentos_plan_strategy_t* agentos_plan_hierarchical_create(
    agentos_llm_service_t* llm,
    int max_depth) {

    if (!llm) return NULL;
    if (max_depth <= 0) max_depth = MAX_DEPTH;

    agentos_plan_strategy_t* strat = (agentos_plan_strategy_t*)malloc(sizeof(agentos_plan_strategy_t));
    if (!strat) return NULL;

    hierarchical_data_t* data = (hierarchical_data_t*)malloc(sizeof(hierarchical_data_t));
    if (!data) {
        free(strat);
        return NULL;
    }

    data->llm = llm;
    data->max_depth = max_depth;
    data->lock = agentos_mutex_create();
    if (!data->lock) {
        free(data);
        free(strat);
        return NULL;
    }

    strat->plan = hierarchical_plan;
    strat->destroy = hierarchical_destroy;
    strat->data = data;

    return strat;
}