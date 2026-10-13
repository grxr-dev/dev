cmake_minimum_required(VERSION 3.20)
project(brainage_aw4_romfree LANGUAGES CXX)
get_filename_component(ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
set(FRAMEWORK "${ROOT}/local/ndsrecomp")
set(RUNNER "${FRAMEWORK}/runner")
add_executable(aw4_provider_test test.cpp fixture_runtime.cpp fixture_bus.cpp fixture_io.cpp
    fixture_scheduler.cpp fixture_spu.cpp
    "${RUNNER}/src/cp15.cpp" "${RUNNER}/src/gpu3d.cpp" "${RUNNER}/src/wifi_net.cpp"
    "${RUNNER}/vendor/melonds/GPU3D.cpp" "${RUNNER}/vendor/melonds/GPU3D_Soft.cpp"
    "${RUNNER}/vendor/melonds/Savestate.cpp")
target_compile_features(aw4_provider_test PRIVATE cxx_std_20)
target_compile_definitions(aw4_provider_test PRIVATE AW4_ROMFREE_CERTIFICATION=1 LIBSLIRP_STATIC_BUILD)
target_compile_options(aw4_provider_test PRIVATE -ffunction-sections -fdata-sections -Wno-unused-parameter)
target_link_options(aw4_provider_test PRIVATE -Wl,--gc-sections -Wl,--exclude-all-symbols)
target_include_directories(aw4_provider_test PRIVATE "${RUNNER}/src" "${RUNNER}/vendor/melonds"
    "${RUNNER}/vendor/melonds/net/libslirp/src" "${RUNNER}/vendor/melonds/net/libslirp/glib"
    "${ROOT}/build/task-o-sdl-runner/vendor/melonds/net/libslirp"
    "${FRAMEWORK}/recompiler/armv4t" "${FRAMEWORK}/recompiler/support"
    "${FRAMEWORK}/external/arm-recomp-core/common")
target_include_directories(aw4_provider_test SYSTEM PRIVATE "${FRAMEWORK}/recompiler/third_party")
target_link_libraries(aw4_provider_test PRIVATE "${ROOT}/build/task-o-sdl-runner/libnds_armv4t.a"
    "${ROOT}/build/task-o-sdl-runner/libnds_support.a"
    "${ROOT}/build/task-o-sdl-runner/vendor/melonds/net/libslirp/libslirp.a" ws2_32 iphlpapi)
foreach(NAME dispatch_timing emu_profile pc_profile host_profile host_prof_ring host_unwind_x64
    network_savestate_guard cart_backup battery_save gpu2d vram title_patches savestate)
    target_sources(aw4_provider_test PRIVATE "${RUNNER}/src/${NAME}.cpp")
endforeach()
foreach(NAME net_ring net_classify net_capture net_replay net_sanitize net_pcap)
    target_sources(aw4_provider_test PRIVATE "${RUNNER}/src/net/${NAME}.cpp")
endforeach()
foreach(NAME Wifi WifiAP)
    target_sources(aw4_provider_test PRIVATE "${RUNNER}/vendor/melonds/${NAME}.cpp")
endforeach()
foreach(NAME Net Net_Slirp PacketDispatcher)
    target_sources(aw4_provider_test PRIVATE "${RUNNER}/vendor/melonds/net/${NAME}.cpp")
endforeach()
target_sources(aw4_provider_test PRIVATE denied.cpp)
