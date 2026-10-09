#pragma once
#include <cstdio>
#include <cstdlib>
#include <map>
#include <utility>
#include "state.h"

inline void task_i_snapshot(uint32_t pc, bool thumb, uint32_t raw, const uint32_t* regs) {
    if (g_nds_active != NDS_ARM9 || thumb || pc < 0x02020000u || pc >= 0x02090000u) return;
    static FILE* output = [] {
        const char* path = std::getenv("NDS_TASK_I_TRACE");
        return path && *path ? std::fopen(path, "wb") : nullptr;
    }();
    if (!output) return;
    uint32_t target = 0;
    const char* kind = nullptr;
    if ((raw & 0x0f000000u) == 0x0b000000u) {
        const int32_t displacement = int32_t(raw << 8) >> 6;
        target = pc + 8 + displacement;
        kind = "bl";
    } else if ((raw & 0x0ffffff0u) == 0x012fff30u ||
               ((raw & 0x0ffffff0u) == 0x012fff10u && (raw & 15u) != 14u)) {
        target = regs[raw & 15u];
        kind = "indirect";
    }
    if (!kind) return;
    static std::map<std::pair<uint32_t, uint32_t>, unsigned> hits;
    static unsigned sequence = 0;
    unsigned& hit = hits[{pc, target}];
    ++hit;
    if (hit > 8 || sequence >= 6000) return;
    ++sequence;
    std::fprintf(output, "{\"sequence\":%u,\"pc\":%u,\"raw\":%u,\"target\":%u,\"kind\":\"%s\",\"hit\":%u,\"system_cycles\":%llu,\"instruction\":%llu,\"r\":[", sequence, pc, raw, target, kind, hit,
                 (unsigned long long)(g_runtime_cycles >> 1), (unsigned long long)g_insn_count[NDS_ARM9]);
    for (unsigned index = 0; index < 16; ++index)
        std::fprintf(output, "%s%u", index ? "," : "", regs[index]);
    std::fputs("],\"mem\":[", output);
    bool comma = false;
    for (unsigned index : {0u, 1u, 2u, 4u, 5u, 13u}) {
        const uint32_t address = regs[index];
        if (address < 0x02000000u || address > 0x023fff80u) continue;
        std::fprintf(output, "%s{\"addr\":%u,\"hex\":\"", comma ? "," : "", address);
        comma = true;
        for (unsigned byte = 0; byte < 128; ++byte)
            std::fprintf(output, "%02x", unsigned(bus_debug_read8(9, address + byte)));
        std::fputs("\"}", output);
    }
    std::fputs("]}\n", output);
    std::fflush(output);
}
