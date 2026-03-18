add_executable(market_d src/main.c src/agent_registry.c src/skill_registry.c src/installer.c src/publisher.c)
target_include_directories(market_d PRIVATE include ${CMAKE_CURRENT_SOURCE_DIR}/../common/include)
