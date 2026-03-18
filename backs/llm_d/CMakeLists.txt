cmake_minimum_required(VERSION 3.20)
project(llm_d VERSION 1.0.0 LANGUAGES C)

find_package(Threads REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(CURL REQUIRED libcurl)
pkg_check_modules(CJSON REQUIRED libcjson)
pkg_check_modules(YAML REQUIRED yaml-0.1)
pkg_check_modules(TIKTOKEN REQUIRED tiktoken)

set(SOURCES
    src/main.c
    src/service.c
    src/providers/provider.c
    src/providers/openai.c
    src/providers/anthropic.c
    src/providers/deepseek.c
    src/providers/local.c
    src/cache.c
    src/cost_tracker.c
    src/token_counter.c
)

add_executable(llm_d ${SOURCES})

target_include_directories(llm_d PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../common/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../../atoms/utils/observability/include
    ${CURL_INCLUDE_DIRS}
    ${CJSON_INCLUDE_DIRS}
    ${YAML_INCLUDE_DIRS}
    ${TIKTOKEN_INCLUDE_DIRS}
)

target_link_libraries(llm_d
    Threads::Threads
    ${CURL_LIBRARIES}
    ${CJSON_LIBRARIES}
    ${YAML_LIBRARIES}
    ${TIKTOKEN_LIBRARIES}
)

install(TARGETS llm_d DESTINATION bin)