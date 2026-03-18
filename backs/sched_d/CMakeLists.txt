add_executable(sched_d src/main.c src/monitor.c src/strategies/weighted.c src/strategies/round_robin.c src/strategies/ml_based.c)
target_include_directories(sched_d PRIVATE include ${CMAKE_CURRENT_SOURCE_DIR}/../common/include)
