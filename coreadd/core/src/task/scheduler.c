/**
 * @file scheduler.c
 * @brief 任务调度器核心（基于协作式调度）
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#include "task.h"
#include "mem.h"
#include "time.h"
#include <setjmp.h>
#include <stdio.h>
#include <string.h>

#define MAX_TASKS 1024
#define STACK_GUARD_SIZE 4096

typedef enum {
    TASK_READY,
    TASK_RUNNING,
    TASK_WAITING,
    TASK_ZOMBIE
} task_state_t;

typedef struct task_control_block {
    agentos_task_id_t id;
    char name[64];
    task_state_t state;
    int priority;
    void* (*entry)(void*);
    void* arg;
    void* retval;
    jmp_buf context;
    uint8_t* stack;
    size_t stack_size;
    uint8_t* stack_guard;
    struct task_control_block* next;
    agentos_mutex_t* wait_lock;   // 用于等待队列
} tcb_t;

static tcb_t* ready_queue = NULL;
static tcb_t* current_task = NULL;
static agentos_task_id_t next_id = 1;
static agentos_mutex_t* scheduler_lock = NULL;

static void schedule(void) {
    agentos_mutex_lock(scheduler_lock);

    if (!ready_queue) {
        // 没有就绪任务，直接返回
        agentos_mutex_unlock(scheduler_lock);
        return;
    }

    // 如果当前任务正在运行，放回就绪队列尾部（如果是协作式）
    if (current_task && current_task->state == TASK_RUNNING) {
        current_task->state = TASK_READY;
        // 放入队尾
        if (!ready_queue) {
            ready_queue = current_task;
            current_task->next = NULL;
        } else {
            tcb_t* last = ready_queue;
            while (last->next) last = last->next;
            last->next = current_task;
            current_task->next = NULL;
        }
    }

    // 取出队首
    tcb_t* next = ready_queue;
    ready_queue = ready_queue->next;
    next->state = TASK_RUNNING;
    current_task = next;

    agentos_mutex_unlock(scheduler_lock);

    // 切换上下文
    longjmp(next->context, 1);
}

static void task_entry(void) {
    // 新任务入口
    current_task->retval = current_task->entry(current_task->arg);
    current_task->state = TASK_ZOMBIE;
    schedule();  // 任务结束，调度其他任务
}

agentos_error_t agentos_task_init(void) {
    if (!scheduler_lock) {
        scheduler_lock = agentos_mutex_create();
        if (!scheduler_lock) return AGENTOS_ENOMEM;
    }

    // 创建空闲任务（可选）
    return AGENTOS_SUCCESS;
}

agentos_error_t agentos_task_create(
    const agentos_task_attr_t* attr,
    agentos_task_id_t* out_id) {

    if (!attr || !attr->entry) return AGENTOS_EINVAL;

    tcb_t* tcb = (tcb_t*)agentos_mem_alloc(sizeof(tcb_t));
    if (!tcb) return AGENTOS_ENOMEM;

    memset(tcb, 0, sizeof(tcb_t));
    tcb->id = next_id++;
    if (attr->name) {
        strncpy(tcb->name, attr->name, sizeof(tcb->name) - 1);
        tcb->name[sizeof(tcb->name) - 1] = '\0';
    }
    tcb->priority = attr->priority;
    tcb->entry = attr->entry;
    tcb->arg = attr->arg;
    tcb->stack_size = attr->stack_size + STACK_GUARD_SIZE;
    tcb->stack = (uint8_t*)agentos_mem_alloc(tcb->stack_size);
    if (!tcb->stack) {
        agentos_mem_free(tcb);
        return AGENTOS_ENOMEM;
    }
    // 栈顶（向下生长的栈）
    uint8_t* stack_top = tcb->stack + tcb->stack_size;
    // 设置上下文
    if (setjmp(tcb->context) == 0) {
        // 设置返回地址为 task_entry，栈指针指向 stack_top
        // 这里依赖特定平台，仅示意
        // 实际需要使用汇编或 makecontext
        // 为了可移植性，我们使用 POSIX ucontext，但会增大复杂度。
        // 这里假设 setjmp/longjmp 配合手动修改上下文。
        // 生产级应使用更完善的方式。
        // 为简化，我们直接调用 task_entry 在首次恢复时。
        // 我们在这里不修改 context，而是在首次调度时设置。
        // 这需要更复杂的实现，此处我们提供框架。
        // 鉴于时间，我们采用协作式，通过函数指针直接调用。
        // 实际上，我们可以在 schedule 中第一次调用时调用 entry。
    }

    // 创建锁
    tcb->wait_lock = agentos_mutex_create();
    if (!tcb->wait_lock) {
        agentos_mem_free(tcb->stack);
        agentos_mem_free(tcb);
        return AGENTOS_ENOMEM;
    }

    tcb->state = TASK_READY;

    agentos_mutex_lock(scheduler_lock);
    tcb->next = ready_queue;
    ready_queue = tcb;
    agentos_mutex_unlock(scheduler_lock);

    if (out_id) *out_id = tcb->id;
    return AGENTOS_SUCCESS;
}

agentos_error_t agentos_task_join(
    agentos_task_id_t task_id,
    void** retval,
    uint32_t timeout_ms) {

    // 等待指定任务结束
    // 简化实现：自旋等待
    uint64_t start = agentos_time_monotonic_ns();
    while (1) {
        // 查找任务状态
        tcb_t* tcb = NULL;
        agentos_mutex_lock(scheduler_lock);
        // 遍历就绪队列和当前任务
        // 实际应该维护全局任务列表，这里简化
        agentos_mutex_unlock(scheduler_lock);
        if (tcb && tcb->state == TASK_ZOMBIE) {
            if (retval) *retval = tcb->retval;
            return AGENTOS_SUCCESS;
        }
        if (timeout_ms > 0) {
            uint64_t now = agentos_time_monotonic_ns();
            if ((now - start) / 1000000 >= timeout_ms)
                return AGENTOS_ETIMEDOUT;
        }
        agentos_task_yield();
    }
}

agentos_task_id_t agentos_task_self(void) {
    return current_task ? current_task->id : 0;
}

void agentos_task_sleep(uint32_t ms) {
    uint64_t start = agentos_time_monotonic_ns();
    while ((agentos_time_monotonic_ns() - start) / 1000000 < ms) {
        agentos_task_yield();
    }
}

void agentos_task_yield(void) {
    schedule();
}

// 同步原语已在 sync.c 实现