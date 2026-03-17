cmake_minimum_required(VERSION 3.20)
project(agentos-habitat VERSION 3.0.0 LANGUAGES C)

find_package(Threads REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBMICROHTTPD REQUIRED libmicrohttpd)
pkg_check_modules(LIBWEBSOCKETS REQUIRED libwebsockets)
pkg_check_modules(CJSON REQUIRED libcjson)

set(SOURCES
    src/server.c
    src/session.c
    src/health.c
    src/telemetry.c
    src/gateway/http_gateway.c
    src/gateway/ws_gateway.c
    src/gateway/stdio_gateway.c
)

add_executable(agentos_habitat ${SOURCES})

target_include_directories(agentos_habitat PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../coreadd/core/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../coreadd/syscall/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../coreadd/utils/observability/include
    ${LIBMICROHTTPD_INCLUDE_DIRS}
    ${LIBWEBSOCKETS_INCLUDE_DIRS}
    ${CJSON_INCLUDE_DIRS}
)

target_link_libraries(agentos_habitat
    agentos_core          # 提供 agentos_time_monotonic_ns 等基础函数
    agentos_utils         # 提供 logger, metrics, trace
    Threads::Threads
    ${LIBMICROHTTPD_LIBRARIES}
    ${LIBWEBSOCKETS_LIBRARIES}
    ${CJSON_LIBRARIES}
)

install(TARGETS agentos_habitat DESTINATION bin)