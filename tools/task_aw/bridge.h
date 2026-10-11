#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <string>
#include <vector>

namespace task_aw {
struct Snapshot {
    std::map<std::string, uint64_t> values;
    std::map<std::string, std::vector<uint8_t>> bytes;
    template<class Value> void copy(const std::string& key, const Value& value) {
        const auto* first = reinterpret_cast<const uint8_t*>(&value);
        bytes[key] = std::vector<uint8_t>(first, first + sizeof(value));
    }
};
enum class Kind { instruction, access_before, access_after, cycle_commit,
                  retired, irq, scheduler, device, arm7, cap_change };
struct Event {
    Kind kind{};
    uint32_t pc=0, address=0, width=0, value=0;
    bool write=false;
    Snapshot state;
};
using Observer = void (*)(const Event&);
inline Observer observer = nullptr;
inline FILE* audit = nullptr;
[[noreturn]] inline void dispose(FILE* output, int code) noexcept;
inline bool enabled() { return observer != nullptr; }
inline void emit(Kind kind, uint32_t pc=0, uint32_t address=0,
                 uint32_t width=0, uint32_t value=0, bool write=false) {
    if (!observer) return;
    try { observer(Event{kind,pc,address,width,value,write,{}}); }
    catch (...) {
        if (audit) std::fputs("{\"event\":\"observer_failure\"}\n", audit);
        dispose(audit,79);
    }
}
[[noreturn]] inline void dispose(FILE* audit, int code) noexcept {
    if (!audit || std::fflush(audit) != 0 || std::fclose(audit) != 0)
        std::_Exit(78);
    std::_Exit(code);
}
inline bool record_snapshot(FILE* output, const Snapshot& snapshot, size_t entries) {
    if (!output) return false;
    std::fprintf(output,"{\"event\":\"snapshot\",\"entries\":%zu,\"values\":{",entries);
    bool first=true;
    for (const auto& item : snapshot.values) {
        std::fprintf(output,"%s\"%s\":%llu",first?"":",",item.first.c_str(),
                     static_cast<unsigned long long>(item.second));
        first=false;
    }
    std::fputs("},\"bytes_hex\":{",output);
    first=true;
    for (const auto& item : snapshot.bytes) {
        std::fprintf(output,"%s\"%s\":\"",first?"":",",item.first.c_str());
        for (auto byte : item.second) std::fprintf(output,"%02x",unsigned(byte));
        std::fputc('"',output);
        first=false;
    }
    std::fputs("}}\n",output);
    return std::ferror(output)==0;
}
}
