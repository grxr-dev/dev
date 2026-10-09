#pragma once

#include <cstdio>
#include <cstdlib>
#include "state.h"

inline FILE* task_c_trace_file() {
    static FILE* output = [] {
        const char* path = std::getenv("NDS_TASK_C_TRACE");
        return path && *path ? std::fopen(path, "wb") : nullptr;
    }();
    return output;
}

inline bool task_c_ram(uint32_t address) {
    return (address >= 0x02000000u && address < 0x02400000u) ||
           (address >= 0x027e0000u && address < 0x02800000u) ||
           (address >= 0x037f8000u && address < 0x03810000u);
}

inline uint32_t task_c_word(int cpu, uint32_t address) {
    uint32_t value = 0;
    for (unsigned index = 0; index < 4; ++index)
        value |= uint32_t(bus_debug_read8(cpu, address + index)) << (8 * index);
    return value;
}

inline void task_c_snapshot(uint32_t pc, bool thumb, const uint32_t* registers) {
    const int cpu = g_nds_active == NDS_ARM9 ? 9 : 7;
    const char* kind = nullptr;
    if (cpu == 9 && pc == 0x0202fa08u) kind = "wrapper";
    if (cpu == 9 && pc == 0x0200de78u) kind = "write_api";
    if (cpu == 9 && pc == 0x0200e080u && registers[1] == 7) kind = "submit";
    if (cpu == 9 && pc == 0x020091b0u && registers[2] == 0x1eb) kind = "fifo_send";
    if (cpu == 7 && pc == 0x037fe230u && registers[1] == 0x1eb) kind = "fifo_receive";
    if (cpu == 7 && pc == 0x03802f48u) kind = "arm7_write";
    if (!kind) return;
    FILE* output = task_c_trace_file();
    if (!output) return;
    const uint32_t shared = pc == 0x0200e080u ? registers[3] : 0x020d4ce0u;
    const bool shared_valid = task_c_ram(shared) && task_c_ram(shared + 23);
    const bool direct = pc == 0x0202fa08u || pc == 0x0200de78u || pc == 0x03802f48u;
    const uint32_t payload = direct ? registers[1] : shared_valid ? task_c_word(cpu, shared + 12) : 0;
    const uint32_t offset = direct ? registers[0] : shared_valid ? task_c_word(cpu, shared + 16) : 0;
    const uint32_t length = direct ? registers[2] : shared_valid ? task_c_word(cpu, shared + 20) : 0;
    const bool payload_valid = length <= 262144u && task_c_ram(payload) &&
                               (!length || task_c_ram(payload + length - 1));
    static uint64_t sequence = 0;
    const uint64_t cycle = g_runtime_cycles;
    std::fprintf(output,
        "{\"sequence\":%llu,\"kind\":\"%s\",\"cpu\":%d,\"pc\":\"0x%08X\","
        "\"thumb\":%s,\"execution\":\"tier3\",\"cpu_cycles\":%llu,\"system_cycles\":%llu,"
        "\"instruction\":%llu,\"lr\":\"0x%08X\",\"shared\":%u,\"shared_valid\":%s,"
        "\"offset\":%u,\"length\":%u,\"payload\":%u,\"payload_valid\":%s,\"r\":[",
        (unsigned long long)++sequence, kind, cpu, pc, thumb ? "true" : "false",
        (unsigned long long)cycle, (unsigned long long)(cpu == 9 ? cycle >> 1 : cycle),
        (unsigned long long)g_insn_count[g_nds_active], registers[14], shared,
        shared_valid ? "true" : "false", offset, length, payload, payload_valid ? "true" : "false");
    for (unsigned index = 0; index < 16; ++index)
        std::fprintf(output, "%s%u", index ? "," : "", registers[index]);
    std::fputs("],\"payload_hex\":\"", output);
    if (payload_valid)
        for (uint32_t index = 0; index < length; ++index)
            std::fprintf(output, "%02x", unsigned(bus_debug_read8(cpu, payload + index)));
    std::fputs("\"}\n", output);
    std::fflush(output);
}
