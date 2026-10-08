#pragma once

#include <cstdio>
#include <cstdlib>

#include "cart_backup.h"
#include "state.h"

inline bool task_a_instruction_active = false;
inline uint32_t task_a_instruction_pc = 0;
inline bool task_a_instruction_thumb = false;
inline bool task_a_hardware_active = false;

struct TaskAInstructionScope {
    bool previous_active = task_a_instruction_active;
    uint32_t previous_pc = task_a_instruction_pc;
    bool previous_thumb = task_a_instruction_thumb;

    TaskAInstructionScope(uint32_t pc, bool thumb) {
        task_a_instruction_active = true;
        task_a_instruction_pc = pc;
        task_a_instruction_thumb = thumb;
    }

    ~TaskAInstructionScope() {
        task_a_instruction_active = previous_active;
        task_a_instruction_pc = previous_pc;
        task_a_instruction_thumb = previous_thumb;
    }
};

struct TaskAHardwareScope {
    bool previous = task_a_hardware_active;
    TaskAHardwareScope() { task_a_hardware_active = true; }
    ~TaskAHardwareScope() { task_a_hardware_active = previous; }
};

inline FILE* task_a_flash_trace_file() {
    static FILE* output = [] {
        const char* path = std::getenv("NDS_FLASH_TRACE");
        if (!path || !*path) return static_cast<FILE*>(nullptr);
        FILE* opened = std::fopen(path, "wb");
        if (!opened) std::fprintf(stderr, "[flash-trace] cannot open %s\n", path);
        return opened;
    }();
    return output;
}

inline NdsCartBackupOrigin task_a_capture_origin() {
    NdsCartBackupOrigin origin;
    origin.cpu = g_nds_active == NDS_ARM9 ? 9u : 7u;
    origin.valid = !task_a_hardware_active;
    origin.execution = task_a_hardware_active ? 3u :
                       task_a_instruction_active ? 2u : 1u;
    if (origin.valid) {
        origin.pc = task_a_instruction_active ? task_a_instruction_pc : g_cpu.R[15];
        origin.thumb = task_a_instruction_active ? task_a_instruction_thumb :
                       (g_cpu.cpsr & 0x20u) != 0u;
    }
    origin.cpu_cycles = g_runtime_cycles;
    origin.system_cycles = origin.cpu == 9u ? g_runtime_cycles >> 1u : g_runtime_cycles;
    origin.instruction = g_insn_count[g_nds_active];
    return origin;
}

inline void task_a_emit_origin(FILE* output, const NdsCartBackupOrigin& origin) {
    const char* execution = origin.execution == 1u ? "native" :
                            origin.execution == 2u ? "tier3" :
                            origin.execution == 3u ? "hardware-unknown" : "unknown";
    std::fprintf(output,
        "{\"valid\":%s,\"cpu\":%u,\"pc\":\"0x%08X\",\"thumb\":%s,"
        "\"execution\":\"%s\",\"cpu_cycles\":%llu,\"system_cycles\":%llu,"
        "\"instruction\":%llu}",
        origin.valid ? "true" : "false", unsigned(origin.cpu), origin.pc,
        origin.thumb ? "true" : "false", execution,
        static_cast<unsigned long long>(origin.cpu_cycles),
        static_cast<unsigned long long>(origin.system_cycles),
        static_cast<unsigned long long>(origin.instruction));
}

inline void task_a_flash_commit(const NdsCartBackup& chip, uint32_t offset,
    const uint8_t* previous, const uint8_t* committed, uint32_t length,
    uint32_t position, bool last) {
    FILE* output = task_a_flash_trace_file();
    if (!output) return;
    static uint64_t sequence = 0;
    uint32_t changed = 0;
    for (uint32_t index = 0; index < length; ++index)
        changed += previous[index] != committed[index] ? 1u : 0u;
    std::fprintf(output,
        "{\"sequence\":%llu,\"transaction\":%llu,\"command\":\"0x%02X\","
        "\"status_before_latch_clear\":%u,\"spi_position\":%u,\"last\":%s,"
        "\"offset\":%u,\"length\":%u,\"changed_bytes\":%u,\"wrap_mask\":%u,"
        "\"commit_path\":\"flash_spi_write\",\"command_origin\":",
        static_cast<unsigned long long>(++sequence),
        static_cast<unsigned long long>(chip.trace_transaction), unsigned(chip.cmd),
        unsigned(chip.status), position, last ? "true" : "false", offset,
        length, changed, static_cast<unsigned>(chip.sram.size() - 1u));
    task_a_emit_origin(output, chip.trace_command_origin);
    std::fputs(",\"byte_origin\":", output);
    task_a_emit_origin(output, chip.trace_byte_origin);
    std::fputs(",\"old_hex\":\"", output);
    for (uint32_t index = 0; index < length; ++index)
        std::fprintf(output, "%02x", unsigned(previous[index]));
    std::fputs("\",\"new_hex\":\"", output);
    for (uint32_t index = 0; index < length; ++index)
        std::fprintf(output, "%02x", unsigned(committed[index]));
    std::fputs("\"}\n", output);
    std::fflush(output);
}
