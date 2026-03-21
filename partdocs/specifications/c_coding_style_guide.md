# AgentOS C 语言编码规范 v1.0.1

**版本**：1.0.1\
**日期**：2026-03-20\
**基于**：工程双论\
**适用范围**：AgentOS 所有 C 语言模块（内核、服务、安全、运行时）

***

## 1. 哲学基础

AgentOS 的每一行代码都应体现三大核心思想：

- **工程控制论**：系统必须具备反馈闭环——通过错误码、日志、健康检查、降级策略形成自调节能力。
- **系统工程**：模块化、接口化、配置驱动。组件职责单一，通过清晰接口协作，追求整体最优。
- **思维双系统**：区分 System 1（快速直觉）与 System 2（深度思考）。代码中提供快速路径（无锁、缓存）与慢速路径（复杂计算、外部调用）的切换机制。
- **乔布斯美学**：代码即艺术品。资源所有权清晰，接口精炼，命名优雅，注释恰到好处。

***

## 2. 文件组织

### 2.1 目录结构

- 按功能划分模块（如 `cognition/`、`execution/`、`workbench/`）。
- 每个模块包含：
  - `include/`：公共头文件（仅对外接口）。
  - `src/`：源文件和内部头文件（实现细节）。
- 内部头文件（如 `module_internal.h`）仅用于模块内共享，不得被其他模块包含。

### 2.2 头文件规范

- 使用 `#ifndef MODULE_H` 保护，命名规则 `<MODULE>_H`。
- 公共类型使用不透明指针（`typedef struct module module_t;`），隐藏内部实现。
- 所有公共函数声明在头文件中，内部函数加 `static` 或放在 `internal.h` 中。
- 头文件必须包含版权声明、简要说明、`extern "C"` 块

### 2.3 源文件规范

- 一个 `.c` 文件对应一个 `.h`，文件名一致。
- 每个源文件行数建议不超过 **500 行**，超过应考虑拆分为多个子模块。
- 文件顶部包含对应头文件，然后是系统头文件和内部头文件。示例：
```c
/**
 * @file service.c
 * @brief 服务核心逻辑实现
 * @copyright (c) 2026 SPHARX Ltd. All Rights Reserved. "From data intelligence emerges."
 */
 ```

***

## 3. 命名规则

- **函数、变量、类型**：全小写，下划线分隔（`snake_case`）。
- **宏、常量**：全大写，下划线分隔（`UPPER_CASE`）。
- **类型名**：以 `_t` 结尾，如 `agentos_error_t`。
- **枚举值**：全大写，带模块前缀，如 `TASK_STATUS_PENDING`。
- **私有函数**：仅用于当前 `.c` 文件的，加 `static`；模块内共享但不公开的，加 `_` 前缀。
- **避免缩写**：除常见缩写（`ctx`、`len`、`ret`、`idx`）外，尽量使用全称。

***

## 4. 函数设计

### 4.1 单一职责

- 每个函数只做一件事，行数不超过 **50 行**。超过 100 行必须分解。

### 4.2 返回值

- 统一返回 `int` 错误码（0 成功，负值失败）。错误码定义在 `agentos_error.h`。
- 返回指针的函数（如 `*_create`），失败返回 `NULL`，调用者通过 `agentos_strerror()` 获取详情。
- 输出参数使用指针，输入参数使用 `const`。

```c
int service_process(service_t* svc, const char* input, char** output);
```

### 4.3 资源分配与释放

- 每个 `*_create` 必须有对应的 `*_destroy`，成对出现。
- 错误路径使用 `goto fail` 模式统一释放资源。

```c
service_t* service_create(const char* path) {
    service_t* svc = calloc(1, sizeof(*svc));
    if (!svc) goto fail;
    svc->file = fopen(path, "r");
    if (!svc->file) goto fail;
    return svc;
fail:
    free(svc);
    return NULL;
}
```

### 4.4 参数检查

- 函数入口必须检查关键参数非空，无效返回 `AGENTOS_EINVAL` 并记录日志。
- 使用 `assert` 仅用于调试内部不变量，生产代码不依赖。

***

## 5. 错误处理

### 5.1 错误码体系

- 统一使用 `agentos_error_t`（`int32_t`），定义在 `core/include/error.h`。
- 范围：0 成功，1–99 保留，100+ 模块自定义（如 `TOOL_ERR_DUPLICATE`）。
- 提供 `const char* agentos_strerror(agentos_error_t err)` 转换错误码。

### 5.2 日志记录

- 使用 `AGENTOS_LOG_ERROR`、`AGENTOS_LOG_WARN`、`AGENTOS_LOG_INFO`、`AGENTOS_LOG_DEBUG` 宏。
- 日志内容应包含模块名、函数名、错误码和关键参数。
- 所有错误路径必须记录 ERROR 级别日志。

### 5.3 错误传播

- 函数返回错误码，调用者必须检查并处理或向上传播。
- 不得静默吞掉错误（如 `if (err) { /* ignore */ }` 必须注释理由）。

***

## 6. 资源管理

### 6.1 内存

- `malloc`/`calloc`/`realloc` 配对 `free`；`strdup` 配对 `free`。
- 尽量使用 `calloc` 清零，避免未初始化数据。
- `realloc` 用临时变量保存新指针，防止丢失原指针。

```c
void* new_ptr = realloc(old_ptr, new_size);
if (!new_ptr) {
    free(old_ptr);
    return NULL;
}
old_ptr = new_ptr;
```

### 6.2 文件、锁、句柄

- `fopen` 配对 `fclose`；`pthread_mutex_lock` 配对 `unlock`。
- 在 `goto fail` 模式中统一释放。

### 6.3 所有权

- 谁分配谁释放。返回分配资源的函数，文档中需说明调用者负责释放。
- 使用 `const` 表示只读访问。

***

## 7. 并发与线程安全

### 7.1 锁粒度

- 使用细粒度锁，避免全局锁。
- 读写分离使用 `pthread_rwlock_t`。
- 避免锁嵌套；若必须嵌套，保持全局一致的加锁顺序。

### 7.2 无锁设计

- 简单计数器使用原子操作（`__sync_fetch_and_add`）。
- 使用 `pthread_cond_t` 实现生产者 - 消费者队列。

### 7.3 健康检查

- 每个长期运行的服务必须提供健康检查函数，返回 JSON 格式状态，包含：
  - 组件状态（"healthy", "degraded", "unhealthy"）
  - 关键指标（队列长度、并发数、错误计数）
  - 最近错误（含时间戳）

```c
int service_health_check(service_t* svc, char** out_json);
```

### 7.4 线程局部存储

- 使用 `pthread_key_t` 存储线程私有数据，避免共享。

***

## 8. 日志与可观测性

### 8.1 结构化日志

- 日志格式为 JSON，字段包括：
  - `timestamp`（Unix 秒级浮点数）
  - `level`（"error", "warn", "info", "debug"）
  - `module`、`function`、`trace_id`、`message`、`err_code` 等

### 8.2 追踪 ID

- 最外层生成唯一 `trace_id`，通过 `agentos_log_set_trace_id` 设置到线程局部存储。
- 下层模块使用 `agentos_log_get_trace_id` 获取，自动包含在日志中。

### 8.3 日志级别

- **DEBUG**：调试信息，生产环境默认关闭。
- **INFO**：关键状态变化（启动、配置加载、任务完成）。
- **WARN**：可恢复异常（重试、降级）。
- **ERROR**：不可恢复错误（资源分配失败、外部服务不可用）。

***

## 9. 配置管理

### 9.1 配置驱动

- 所有可变参数（超时、重试、缓存大小、定价）必须从 YAML 文件加载，禁止硬编码。
- 使用 `config_loader.h` 加载 YAML，返回 `cJSON`。

### 9.2 默认值

- 每个配置项必须提供合理的默认值，保证服务无配置也能启动。

### 9.3 热加载

- 支持通过信号（如 `SIGHUP`）或接口通知服务重新加载配置，无需重启。

### 9.4 环境变量覆盖

- 支持环境变量覆盖配置，格式：`AGENTOS_SECTION_KEY`。

***

## 10. 测试与可测性

### 10.1 依赖注入

- 模块依赖通过接口指针传入，便于单元测试时替换为 mock 实现。

```c
typedef struct llm_ops {
    int (*complete)(void* ctx, const char* prompt, char** out);
} llm_ops_t;

struct llm_service {
    const llm_ops_t* ops;
    void* priv;
};
```

### 10.2 单元测试

- 使用 `cmocka` 或 `check` 框架，每个模块至少覆盖正常路径、错误路径、边界条件。
- 测试文件放在 `tests/` 子目录，命名 `test_module.c`。

### 10.3 集成测试

- 通过 `habitat` 网关或模拟客户端测试服务间交互。

***

## 11. 代码美学与风格

### 11.1 行宽

- 推荐 80 字符，不超过 100 字符。避免因过度折行影响可读性。

### 11.2 空白

- 函数间空两行，逻辑块间空一行。
- 二元运算符两侧加空格（`a = b + c`），逗号后加空格（`func(a, b)`）。

### 11.3 函数签名对齐

```c
int some_function(
    const char* param1,
    int param2,
    struct complex_type* param3)
{
    // ...
}
```

### 11.4 结构体成员对齐

```c
typedef struct service {
    char*   name;           /**< 服务名称 */
    int     port;           /**< 端口号 */
    size_t  max_queue;      /**< 最大队列长度 */
} service_t;
```

### 11.5 注释

- 文件头：版权、简要说明。
- 函数头：使用 Doxygen 风格 `@brief`、`@param`、`@return`。
- 复杂逻辑：行内注释解释“为什么”，而非“做什么”。
- 代码本身应自解释，避免冗余注释。

### 11.6 避免重复代码

- 复用公共函数，禁止复制粘贴。

***

## 12. 双系统思维实践

### 12.1 System 1 快速路径

- 无锁、无阻塞、低开销操作，如缓存命中、简单数学计算、本地状态检查。
- 使用原子操作、无锁数据结构（如环形缓冲区 + 条件变量）。

### 12.2 System 2 深度路径

- 复杂计算、外部调用、IO 操作，需带超时、重试、降级。
- 使用互斥锁、条件变量，并设置合理超时。
- 提供降级策略（如 LLM 服务不可用时使用本地规则或缓存）。

### 12.3 切换机制

- 代码中显式区分快速路径与慢速路径：

```c
if (cache_hit) {
    return cached_result;  // System 1
}
// System 2
result = call_external_api();
cache_store(result);
return result;
```

- 使用策略模式（函数指针）允许运行时选择不同算法（如调度策略）。

***

## 13. 安全编程实践

### 13.1 字符串安全

- 使用 `snprintf` 代替 `sprintf`。
- 使用 `strncpy` 并手动添加 `\0`，或使用 `strlcpy`（若可用）。
- 避免 `gets`、`scanf` 等不安全函数。

### 13.2 缓冲区溢出防护

- 固定大小数组操作前检查长度。
- 动态分配内存时确保大小非零且合理。

### 13.3 指针安全

- 函数参数指针在使用前检查非空。
- 释放后立即置 `NULL`，避免悬垂指针。

### 13.4 整数溢出

- 在加、乘等操作前检查溢出，尤其是大小计算（如 `size * sizeof(type)`）。

### 13.5 编译警告

- 编译时开启 `-Wall -Wextra -Werror`，将所有警告视为错误。

***

## 14. 工具链与构建

### 14.1 CMake 构建

- 每个模块提供 `CMakeLists.txt`，使用 `add_library` 或 `add_executable`。
- 使用 `target_include_directories` 管理头文件路径。
- 使用 `pkg_check_modules` 查找外部依赖。

### 14.2 静态分析

- 定期使用 `clang-tidy` 或 `cppcheck` 进行静态分析。

### 14.3 代码格式化

- 使用 `clang-format` 统一风格，提供 `.clang-format` 文件。

***

## 15. 演进与遵守

本规范是项目长期实践的总结，体现了控制论的反馈闭环、系统工程的层次分解、双系统的分工协同与乔布斯美学的极致追求。它随项目演进持续迭代，所有新代码必须遵守，旧代码逐步重构以对齐。

代码的每一处细节，都是系统哲学的外显；内部的美学，最终外化为用户可感知的稳健与优雅。

维护者：LirenWang;ChenZhang;DechengLi
最后更新：2026-03-20

***

© 2026 SPHARX Ltd. All Rights Reserved.
