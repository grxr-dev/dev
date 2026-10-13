#include <cstdlib>
#include <string>
#include "coverage_manifest.h"
#include "live_overlay.h"
#include "diagnostics.h"
#include "state.h"
uint64_t g_coverage_write_epoch=0;
CoverageExecCache g_coverage_exec_cache[2]{};
void coverage_capture_exec_page(int,uint32_t,uint32_t) { std::abort(); }
void coverage_note_generation_entry(int,uint32_t,bool,uint8_t,uint32_t) { std::abort(); }
void live_overlay_runtime_reset() { std::abort(); }
void live_overlay_note_cached_hit(uint32_t) { std::abort(); }
void live_overlay_note_transfer(int,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t) { std::abort(); }
void live_overlay_note_lookup(int,uint32_t,uint32_t,uint32_t,uint32_t,const NdsDispatchEntry*,const NdsDispatchEntry*,uint32_t,const char*) { std::abort(); }
uint32_t live_overlay_candidate_serial(int,const NdsDispatchEntry* entry) {
    if (entry && !entry->validation) return 0;
    std::abort();
}
void live_overlay_note_write(int,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t) { std::abort(); }
void live_overlay_poll() { std::abort(); }
bool nds_diagnostics_enabled() { return false; }
std::string nds_diagnostics_dispatch_miss_log_path() { std::abort(); }
void tier3_reset() { std::abort(); }
void tier3_note_clean_ram_reject() { std::abort(); }
void tier3_run(uint32_t) { std::abort(); }
