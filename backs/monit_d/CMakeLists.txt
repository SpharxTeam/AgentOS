add_executable(monit_d src/main.c src/metrics.c src/tracing.c src/alert.c src/logging.c)
target_include_directories(monit_d PRIVATE include ${CMAKE_CURRENT_SOURCE_DIR}/../common/include)
