/**
 * @file performance_test.c
 * @brief 性能测试工具
 * @details 测试系统在高并发场景下的稳定性和响应时间
 * @copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <cjson/cJSON.h>

#define MAX_THREADS 100
#define MAX_REQUESTS 1000
#define SOCKET_PATH_LLM "/var/run/agentos/llm.sock"
#define SOCKET_PATH_SCHED "/var/run/agentos/sched.sock"
#define SOCKET_PATH_TOOL "/var/run/agentos/tool.sock"

/**
 * @brief 测试结果结构
 */
typedef struct {
    int total_requests;
    int successful_requests;
    int failed_requests;
    double total_time_ms;
    double min_time_ms;
    double max_time_ms;
    double avg_time_ms;
} test_result_t;

/**
 * @brief 线程参数结构
 */
typedef struct {
    int thread_id;
    int num_requests;
    const char* socket_path;
    const char* service_type;
    test_result_t* result;
    pthread_mutex_t* mutex;
} thread_args_t;

/**
 * @brief 发送 JSON-RPC 请求
 * @param socket_fd 套接字文件描述符
 * @param method 方法名
 * @param params 参数 JSON
 * @param id 请求 ID
 * @return 0 表示成功，非 0 表示失败
 */
static int send_jsonrpc_request(int socket_fd, const char* method, const char* params, int id) {
    cJSON* root = cJSON_CreateObject();
    cJSON_AddStringToObject(root, "jsonrpc", "2.0");
    cJSON_AddStringToObject(root, "method", method);
    cJSON* params_obj = cJSON_Parse(params);
    if (params_obj) {
        cJSON_AddItemToObject(root, "params", params_obj);
    } else {
        cJSON_AddNullToObject(root, "params");
    }
    cJSON_AddNumberToObject(root, "id", id);
    
    char* json_str = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);
    
    if (!json_str) {
        return -1;
    }
    
    ssize_t sent = write(socket_fd, json_str, strlen(json_str));
    free(json_str);
    
    return (sent > 0) ? 0 : -1;
}

/**
 * @brief 接收 JSON-RPC 响应
 * @param socket_fd 套接字文件描述符
 * @param buffer 缓冲区
 * @param buffer_size 缓冲区大小
 * @return 读取的字节数
 */
static ssize_t receive_jsonrpc_response(int socket_fd, char* buffer, size_t buffer_size) {
    return read(socket_fd, buffer, buffer_size - 1);
}

/**
 * @brief 连接到 Unix socket 服务
 * @param socket_path 套接字路径
 * @return 套接字文件描述符，失败返回 -1
 */
static int connect_to_service(const char* socket_path) {
    int sockfd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (sockfd < 0) {
        return -1;
    }
    
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, socket_path, sizeof(addr.sun_path) - 1);
    
    if (connect(sockfd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        close(sockfd);
        return -1;
    }
    
    return sockfd;
}

/**
 * @brief 测试 LLM 服务
 * @param args 线程参数
 * @return 线程返回值
 */
static void* test_llm_service(void* args) {
    thread_args_t* targs = (thread_args_t*)args;
    
    for (int i = 0; i < targs->num_requests; i++) {
        int sockfd = connect_to_service(targs->socket_path);
        if (sockfd < 0) {
            pthread_mutex_lock(targs->mutex);
            targs->result->failed_requests++;
            pthread_mutex_unlock(targs->mutex);
            continue;
        }
        
        double start_time = (double)clock() / CLOCKS_PER_SEC * 1000.0;
        
        const char* params = "{\"model\": \"gpt-3.5-turbo\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello, how are you?\"}], \"temperature\": 0.7, \"max_tokens\": 50, \"stream\": false}";
        int ret = send_jsonrpc_request(sockfd, "complete", params, targs->thread_id * targs->num_requests + i);
        
        if (ret == 0) {
            char buffer[65536];
            ssize_t n = receive_jsonrpc_response(sockfd, buffer, sizeof(buffer));
            if (n > 0) {
                double end_time = (double)clock() / CLOCKS_PER_SEC * 1000.0;
                double elapsed = end_time - start_time;
                
                pthread_mutex_lock(targs->mutex);
                targs->result->successful_requests++;
                targs->result->total_time_ms += elapsed;
                if (elapsed < targs->result->min_time_ms || targs->result->min_time_ms == 0) {
                    targs->result->min_time_ms = elapsed;
                }
                if (elapsed > targs->result->max_time_ms) {
                    targs->result->max_time_ms = elapsed;
                }
                pthread_mutex_unlock(targs->mutex);
            } else {
                pthread_mutex_lock(targs->mutex);
                targs->result->failed_requests++;
                pthread_mutex_unlock(targs->mutex);
            }
        } else {
            pthread_mutex_lock(targs->mutex);
            targs->result->failed_requests++;
            pthread_mutex_unlock(targs->mutex);
        }
        
        close(sockfd);
    }
    
    return NULL;
}

/**
 * @brief 测试调度服务
 * @param args 线程参数
 * @return 线程返回值
 */
static void* test_sched_service(void* args) {
    thread_args_t* targs = (thread_args_t*)args;
    
    for (int i = 0; i < targs->num_requests; i++) {
        int sockfd = connect_to_service(targs->socket_path);
        if (sockfd < 0) {
            pthread_mutex_lock(targs->mutex);
            targs->result->failed_requests++;
            pthread_mutex_unlock(targs->mutex);
            continue;
        }
        
        double start_time = (double)clock() / CLOCKS_PER_SEC * 1000.0;
        
        const char* params = "{\"task_id\": \"task_\", \"task_description\": \"Test task\", \"priority\": 1, \"timeout_ms\": 5000}";
        int ret = send_jsonrpc_request(sockfd, "schedule_task", params, targs->thread_id * targs->num_requests + i);
        
        if (ret == 0) {
            char buffer[65536];
            ssize_t n = receive_jsonrpc_response(sockfd, buffer, sizeof(buffer));
            if (n > 0) {
                double end_time = (double)clock() / CLOCKS_PER_SEC * 1000.0;
                double elapsed = end_time - start_time;
                
                pthread_mutex_lock(targs->mutex);
                targs->result->successful_requests++;
                targs->result->total_time_ms += elapsed;
                if (elapsed < targs->result->min_time_ms || targs->result->min_time_ms == 0) {
                    targs->result->min_time_ms = elapsed;
                }
                if (elapsed > targs->result->max_time_ms) {
                    targs->result->max_time_ms = elapsed;
                }
                pthread_mutex_unlock(targs->mutex);
            } else {
                pthread_mutex_lock(targs->mutex);
                targs->result->failed_requests++;
                pthread_mutex_unlock(targs->mutex);
            }
        } else {
            pthread_mutex_lock(targs->mutex);
            targs->result->failed_requests++;
            pthread_mutex_unlock(targs->mutex);
        }
        
        close(sockfd);
    }
    
    return NULL;
}

/**
 * @brief 测试工具服务
 * @param args 线程参数
 * @return 线程返回值
 */
static void* test_tool_service(void* args) {
    thread_args_t* targs = (thread_args_t*)args;
    
    for (int i = 0; i < targs->num_requests; i++) {
        int sockfd = connect_to_service(targs->socket_path);
        if (sockfd < 0) {
            pthread_mutex_lock(targs->mutex);
            targs->result->failed_requests++;
            pthread_mutex_unlock(targs->mutex);
            continue;
        }
        
        double start_time = (double)clock() / CLOCKS_PER_SEC * 1000.0;
        
        const char* params = "{\"tool_id\": \"test-tool\", \"params\": {\"message\": \"Hello, World!\"}}";
        int ret = send_jsonrpc_request(sockfd, "execute_tool", params, targs->thread_id * targs->num_requests + i);
        
        if (ret == 0) {
            char buffer[65536];
            ssize_t n = receive_jsonrpc_response(sockfd, buffer, sizeof(buffer));
            if (n > 0) {
                double end_time = (double)clock() / CLOCKS_PER_SEC * 1000.0;
                double elapsed = end_time - start_time;
                
                pthread_mutex_lock(targs->mutex);
                targs->result->successful_requests++;
                targs->result->total_time_ms += elapsed;
                if (elapsed < targs->result->min_time_ms || targs->result->min_time_ms == 0) {
                    targs->result->min_time_ms = elapsed;
                }
                if (elapsed > targs->result->max_time_ms) {
                    targs->result->max_time_ms = elapsed;
                }
                pthread_mutex_unlock(targs->mutex);
            } else {
                pthread_mutex_lock(targs->mutex);
                targs->result->failed_requests++;
                pthread_mutex_unlock(targs->mutex);
            }
        } else {
            pthread_mutex_lock(targs->mutex);
            targs->result->failed_requests++;
            pthread_mutex_unlock(targs->mutex);
        }
        
        close(sockfd);
    }
    
    return NULL;
}

/**
 * @brief 运行性能测试
 * @param service_type 服务类型
 * @param socket_path 套接字路径
 * @param num_threads 线程数
 * @param num_requests 每个线程的请求数
 * @return 测试结果
 */
static test_result_t run_performance_test(const char* service_type, const char* socket_path, int num_threads, int num_requests) {
    test_result_t result = {
        .total_requests = num_threads * num_requests,
        .successful_requests = 0,
        .failed_requests = 0,
        .total_time_ms = 0.0,
        .min_time_ms = 0.0,
        .max_time_ms = 0.0,
        .avg_time_ms = 0.0
    };
    
    pthread_t threads[MAX_THREADS];
    thread_args_t thread_args[MAX_THREADS];
    pthread_mutex_t mutex;
    
    pthread_mutex_init(&mutex, NULL);
    
    for (int i = 0; i < num_threads; i++) {
        thread_args[i].thread_id = i;
        thread_args[i].num_requests = num_requests;
        thread_args[i].socket_path = socket_path;
        thread_args[i].service_type = service_type;
        thread_args[i].result = &result;
        thread_args[i].mutex = &mutex;
        
        if (strcmp(service_type, "llm") == 0) {
            pthread_create(&threads[i], NULL, test_llm_service, &thread_args[i]);
        } else if (strcmp(service_type, "sched") == 0) {
            pthread_create(&threads[i], NULL, test_sched_service, &thread_args[i]);
        } else if (strcmp(service_type, "tool") == 0) {
            pthread_create(&threads[i], NULL, test_tool_service, &thread_args[i]);
        }
    }
    
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    pthread_mutex_destroy(&mutex);
    
    if (result.successful_requests > 0) {
        result.avg_time_ms = result.total_time_ms / result.successful_requests;
    }
    
    return result;
}

/**
 * @brief 打印测试结果
 * @param service_type 服务类型
 * @param result 测试结果
 */
static void print_test_result(const char* service_type, test_result_t result) {
    printf("=== Performance Test Results for %s Service ===\n", service_type);
    printf("Total Requests: %d\n", result.total_requests);
    printf("Successful Requests: %d\n", result.successful_requests);
    printf("Failed Requests: %d\n", result.failed_requests);
    printf("Success Rate: %.2f%%\n", (double)result.successful_requests / result.total_requests * 100.0);
    printf("Total Time: %.2f ms\n", result.total_time_ms);
    printf("Minimum Response Time: %.2f ms\n", result.min_time_ms);
    printf("Maximum Response Time: %.2f ms\n", result.max_time_ms);
    printf("Average Response Time: %.2f ms\n", result.avg_time_ms);
    printf("Requests Per Second: %.2f\n", (double)result.successful_requests / (result.total_time_ms / 1000.0));
    printf("==============================================\n\n");
}

/**
 * @brief 主函数
 * @return 0 表示成功，非 0 表示失败
 */
int main(int argc, char** argv) {
    if (argc < 2) {
        printf("Usage: %s <service_type> [num_threads] [num_requests_per_thread]\n", argv[0]);
        printf("Service types: llm, sched, tool\n");
        return 1;
    }
    
    const char* service_type = argv[1];
    int num_threads = (argc > 2) ? atoi(argv[2]) : 10;
    int num_requests = (argc > 3) ? atoi(argv[3]) : 100;
    
    if (num_threads > MAX_THREADS) {
        num_threads = MAX_THREADS;
    }
    
    if (num_requests > MAX_REQUESTS) {
        num_requests = MAX_REQUESTS;
    }
    
    const char* socket_path = NULL;
    if (strcmp(service_type, "llm") == 0) {
        socket_path = SOCKET_PATH_LLM;
    } else if (strcmp(service_type, "sched") == 0) {
        socket_path = SOCKET_PATH_SCHED;
    } else if (strcmp(service_type, "tool") == 0) {
        socket_path = SOCKET_PATH_TOOL;
    } else {
        printf("Invalid service type: %s\n", service_type);
        return 1;
    }
    
    printf("Running performance test for %s service with %d threads and %d requests per thread...\n\n", 
           service_type, num_threads, num_requests);
    
    test_result_t result = run_performance_test(service_type, socket_path, num_threads, num_requests);
    print_test_result(service_type, result);
    
    return 0;
}
