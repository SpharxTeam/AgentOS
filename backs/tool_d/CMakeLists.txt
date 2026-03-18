add_executable(tool_d src/main.c src/registry.c src/executor.c src/validator.c)
target_include_directories(tool_d PRIVATE include ${CMAKE_CURRENT_SOURCE_DIR}/../common/include)
