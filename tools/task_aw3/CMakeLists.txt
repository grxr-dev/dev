cmake_minimum_required(VERSION 3.20)
project(brainage_aw3_romfree LANGUAGES CXX)
get_filename_component(ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
set(FRAMEWORK "${ROOT}/local/ndsrecomp")
set(RUNNER "${FRAMEWORK}/runner")
add_executable(aw3_runtime_test
    native.cpp
    "${RUNNER}/tests/savestate_test_stubs.cpp"
    "${RUNNER}/src/savestate.cpp"
    "${RUNNER}/src/bus.cpp"
    "${RUNNER}/src/cp15.cpp"
    "${RUNNER}/src/scheduler.cpp"
    "${RUNNER}/src/spu.cpp"
    "${RUNNER}/src/runtime_arm.cpp"
    "${RUNNER}/src/dispatch_timing.cpp"
    "${RUNNER}/src/emu_profile.cpp"
    "${RUNNER}/src/pc_profile.cpp")
target_compile_features(aw3_runtime_test PRIVATE cxx_std_20)
target_compile_options(aw3_runtime_test PRIVATE -Wall -Wextra -Wno-unused-parameter)
target_include_directories(aw3_runtime_test PRIVATE
    "${RUNNER}/src" "${RUNNER}/vendor/melonds"
    "${FRAMEWORK}/recompiler/armv4t" "${FRAMEWORK}/recompiler/support"
    "${FRAMEWORK}/external/arm-recomp-core/common")
target_include_directories(aw3_runtime_test SYSTEM PRIVATE "${FRAMEWORK}/recompiler/third_party")
target_link_libraries(aw3_runtime_test PRIVATE
    "${ROOT}/build/task-o-sdl-runner/libnds_armv4t.a"
    "${ROOT}/build/task-o-sdl-runner/libnds_support.a")
