# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# backs 顶层构建文件
cmake_minimum_required(VERSION 3.20)
project(agentos-backs VERSION 1.0.0.3 LANGUAGES C)

add_subdirectory(llm_d)
add_subdirectory(tool_d)
add_subdirectory(market_d)
add_subdirectory(sched_d)
add_subdirectory(monit_d)
