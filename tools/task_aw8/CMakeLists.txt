cmake_minimum_required(VERSION 3.20)
project(brainage_aw8_romfree LANGUAGES CXX)
get_filename_component(ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
set(FRAMEWORK "${ROOT}/local/ndsrecomp")
set(RUNNER "${FRAMEWORK}/runner")
if(NOT DEFINED AW8_GENERATED)
    message(FATAL_ERROR "Use check.py with authenticated local evidence")
endif()
add_executable(aw8_provider_test test.cpp runtime.cpp bus.cpp io.cpp scheduler.cpp spu.cpp cp15.cpp
    "${ROOT}/tools/task_aw4/denied.cpp" "${RUNNER}/src/gpu3d.cpp" "${RUNNER}/src/wifi_net.cpp"
    "${RUNNER}/vendor/melonds/GPU3D.cpp" "${RUNNER}/vendor/melonds/GPU3D_Soft.cpp"
    "${RUNNER}/vendor/melonds/Savestate.cpp")
target_compile_features(aw8_provider_test PRIVATE cxx_std_20)
target_compile_definitions(aw8_provider_test PRIVATE AW8_ROMFREE_FIXTURE=1 AW7_DIAGNOSTIC_HARNESS=1 AW7_ROMFREE_MODEL=1 LIBSLIRP_STATIC_BUILD)
target_compile_options(aw8_provider_test PRIVATE -ffunction-sections -fdata-sections -Wno-unused-parameter)
target_link_options(aw8_provider_test PRIVATE -Wl,--gc-sections -Wl,--exclude-all-symbols)
target_include_directories(aw8_provider_test PRIVATE "${AW8_GENERATED}" "${RUNNER}/src" "${RUNNER}/vendor/melonds"
    "${RUNNER}/vendor/melonds/net/libslirp/src" "${RUNNER}/vendor/melonds/net/libslirp/glib"
    "${ROOT}/build/task-o-sdl-runner/vendor/melonds/net/libslirp"
    "${FRAMEWORK}/recompiler/armv4t" "${FRAMEWORK}/recompiler/support" "${FRAMEWORK}/external/arm-recomp-core/common")
target_include_directories(aw8_provider_test SYSTEM PRIVATE "${FRAMEWORK}/recompiler/third_party")
target_link_libraries(aw8_provider_test PRIVATE "${ROOT}/build/task-o-sdl-runner/libnds_armv4t.a"
    "${ROOT}/build/task-o-sdl-runner/libnds_support.a"
    "${ROOT}/build/task-o-sdl-runner/vendor/melonds/net/libslirp/libslirp.a" ws2_32 iphlpapi)
foreach(NAME dispatch_timing emu_profile pc_profile host_profile host_prof_ring host_unwind_x64
    network_savestate_guard cart_backup battery_save gpu2d vram title_patches savestate)
    target_sources(aw8_provider_test PRIVATE "${RUNNER}/src/${NAME}.cpp")
endforeach()
foreach(NAME net_ring net_classify net_capture net_replay net_sanitize net_pcap)
    target_sources(aw8_provider_test PRIVATE "${RUNNER}/src/net/${NAME}.cpp")
endforeach()
foreach(NAME Wifi WifiAP)
    target_sources(aw8_provider_test PRIVATE "${RUNNER}/vendor/melonds/${NAME}.cpp")
endforeach()
foreach(NAME Net Net_Slirp PacketDispatcher)
    target_sources(aw8_provider_test PRIVATE "${RUNNER}/vendor/melonds/net/${NAME}.cpp")
endforeach()
