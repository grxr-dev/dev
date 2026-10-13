#pragma once
#include <thread>
#include "sha1.h"
#include "../task_aw2/controller.h"
#if defined(_WIN32)
#include <fcntl.h>
extern "C" {
_CRTIMP int __cdecl _open(const char*,int,...);
_CRTIMP int __cdecl _close(int);
}
#endif

namespace task_aw3 {
using task_aw2::Snapshot;
using task_aw2::require;
struct CapRecord {
    uint64_t epoch=0,serial=0,cycle=0,before=0,after=0,deadline=0;
    uint32_t cpu=0,source=0;
};
inline bool armed=false;
inline FILE* output=nullptr;
inline uint64_t epoch=0,serial=0,rom_epoch=0,logical_saves=0,flash_commits=0;
inline std::thread::id owner;
inline std::vector<CapRecord> history;
inline std::string sticky,rom_identity;
inline bool bound=false;
inline Snapshot immutable;
inline std::string immutable_digest;
inline FILE* exclusive_audit(const char* path) {
    if (!path || !*path) return nullptr;
#if defined(_WIN32)
    const int descriptor=_open(path,_O_CREAT|_O_EXCL|_O_WRONLY|_O_BINARY|_O_NOINHERIT,0600);
    if (descriptor<0) return nullptr;
    auto* file=_fdopen(descriptor,"wb");
    if (!file) _close(descriptor);
    return file;
#else
    return std::fopen(path,"wbx");
#endif
}
inline void audit_text(const char* event, const std::string& reason) noexcept {
    if (!output) return;
    std::fprintf(output,"{\"event\":\"%s\",\"reason\":\"",event);
    for (unsigned char character:reason) {
        if (character=='"' || character=='\\') std::fputc('\\',output);
        if (character<32) std::fprintf(output,"\\u%04x",unsigned(character));
        else std::fputc(character,output);
    }
    std::fputs("\"}\n",output);
}
[[noreturn]] inline void fail(const std::string& reason) noexcept {
    audit_text("failure",reason);
    task_aw::dispose(output,output && !std::ferror(output) ? 79 : 78);
}
inline void arm(FILE* file) {
    require(file && !armed, "capture ownership");
    output=file;
    owner=std::this_thread::get_id();
    armed=true;
}
inline void loaded_rom(const uint8_t* bytes,size_t size) {
    if (!armed) {
        const char* selector=std::getenv("NDS_TASK_AW3_CAPTURE_ONLY");
        if (!selector || std::string(selector)!="1") return;
        const char* path=std::getenv("NDS_TASK_AW3_AUDIT");
        if (!path || !*path) fail("capture audit path missing");
        auto* file=exclusive_audit(path);
        if (!file) fail("capture audit must be fresh and writable");
        arm(file);
    }
    try {
        require(!bound && bytes && size,"ROM load after seal or missing bytes");
        rom_identity=gba::sha1(bytes,size).hex();
        rom_epoch=task_aw2::add(rom_epoch,1);
        require(rom_identity==task_aw2::au_manifest().hashes.at("rom"),"actual loader ROM identity mismatch");
    } catch (const std::exception& error) { fail(error.what()); }
}
inline void cap_note(uint32_t source,uint32_t cpu,uint64_t cycle,uint64_t before,
                     uint64_t after,uint64_t deadline=0) noexcept {
    if (!armed) return;
    try {
        require(owner==std::this_thread::get_id(),"cap mutation off owner thread");
        require(!bound,"cap mutation after immutable seal");
        if (source==0 || source>1) {
            epoch=task_aw2::add(epoch,1);
            history.clear();
            sticky.clear();
        }
        require(epoch && serial!=UINT64_MAX && history.size()<64,"cap epoch/serial/bounds");
        if (source>1) sticky="unclassified direct cap setter or state import";
        if (!history.empty()) require(history.back().after==before,"cap mutation chain lost");
        if (source==1) {
            const auto target=cpu==0 ? task_aw2::twice(deadline) : deadline;
            require(after==(before ? std::min(before,target) : target),"runtime cap arithmetic disagrees");
        }
        history.push_back({epoch,++serial,cycle,before,after,deadline,cpu,source});
    } catch (const std::exception& error) { fail(error.what()); }
    catch (...) { fail("cap journal exception"); }
}
inline void invalidate() noexcept {
    if (!armed) return;
    if (epoch==UINT64_MAX) fail("capture epoch overflow");
    ++epoch;
    history.clear();
    sticky="state import/reset invalidates cap provenance";
    if (bound) fail("state import after immutable seal");
}
inline void reschedule(uint32_t cpu,uint64_t cycle,uint64_t before,uint64_t deadline) noexcept {
    if (!armed) return;
    try {
        const auto target=cpu==0 ? task_aw2::twice(deadline) : deadline;
        cap_note(1,cpu,cycle,before,before ? std::min(before,target) : target,deadline);
    } catch (const std::exception& error) { fail(error.what()); }
    catch (...) { fail("reschedule provenance exception"); }
}
inline void export_history(Snapshot& out) {
    require(armed && owner==std::this_thread::get_id(),"provider owner");
    require(sticky.empty() && !history.empty(),"missing/stale cap journal");
    out.put("capture.epoch",8,epoch);
    out.put("capture.serial",8,serial);
    out.put("capture.rom_epoch",8,rom_epoch);
    out.put("cap.count",4,history.size());
    for (unsigned index=0;index<history.size();++index) {
        const auto& record=history[index];
        require(record.epoch==epoch && record.cpu==0,"wrong cap epoch/CPU");
        const auto prefix="cap."+std::to_string(index)+".";
        out.put(prefix+"kind",1,record.source);
        out.put(prefix+"cpu",1,record.cpu);
        out.put(prefix+"cycle",8,record.cycle);
        out.put(prefix+"before",8,index ? record.before : 0);
        out.put(prefix+"after",8,record.after);
        out.put(prefix+"base",8,index ? 0 : record.cycle);
        require(index || record.after>=record.cycle,"slice target before base");
        out.put(prefix+"quantum",8,index ? 0 : record.after-record.cycle);
        out.put(prefix+"deadline",8,record.deadline);
        out.put(prefix+"serial",8,record.serial);
        out.put(prefix+"observed_before",8,record.before);
    }
}
void scheduler_snapshot(Snapshot&);
void runtime_snapshot(Snapshot&);
void bus_snapshot(Snapshot&);
void io_snapshot(Snapshot&);
void cp15_snapshot(Snapshot&);
inline Snapshot passive() {
    Snapshot out;
    export_history(out);
    scheduler_snapshot(out);
    require(out.get("owner_thread")==1,"scheduler snapshot wrong thread");
    runtime_snapshot(out);
    bus_snapshot(out);
    io_snapshot(out);
    cp15_snapshot(out);
    require(out.get("capture.end_cycle")==out.get("cycle9") &&
            out.get("capture.end_ordinal")==out.get("ordinal9"),"torn passive snapshot");
    return out;
}
inline Snapshot core_projection(const Snapshot& full) {
    Snapshot core;
    for (const auto& item:task_aw2::layout(full)) {
        const auto found=full.fields.find(item.first);
        require(found!=full.fields.end() && found->second.width==item.second,"missing core projection");
        core.fields[item.first]=found->second;
    }
    core.hashes=full.hashes;
    for (auto iterator=core.hashes.begin();iterator!=core.hashes.end();) {
        if (!task_aw2::au_manifest().hashes.count(iterator->first)) iterator=core.hashes.erase(iterator);
        else ++iterator;
    }
    return core;
}
inline void entry_preflight(const Snapshot& full
#if defined(AW4_ROMFREE_CERTIFICATION)
    , const Snapshot& authority=task_aw2::au_manifest()
#endif
) {
    require(full.get("capture.epoch")==epoch && full.get("capture.serial")==serial &&
            full.get("capture.rom_epoch")==rom_epoch && rom_epoch,"stale provider/ROM epoch");
    require(full.hashes.at("rom")==rom_identity,"ROM loader binding mismatch");
    require(full.get("hidden.code_pc9")==0x0200197c && full.get("hidden.data_addr9")==0x020019a8,
            "AU preceding instruction/access latch mismatch");
    require(full.get("hidden.cache_page")==0x02001000 && full.get("hidden.cache_generation")==full.get("cp15.generation") &&
            full.get("hidden.cache_class")==1 && full.get("hidden.region_valid")==1 &&
            full.get("hidden.region_class")==1 && full.get("hidden.class_ready")==1,"hidden timing latch mismatch");
    for (const auto address:task_aw2::pcs)
        require(full.get(task_aw2::address_key("hidden.code_bit.",address))==task_aw2::cacheable(full,address,true),"stale code bitmap");
    for (const uint32_t address:{0x020019acu,0x020019e4u,0x04000280u,0x04000290u,0x04000294u,0x04000298u,0x0400029cu})
        require(full.get(task_aw2::address_key("hidden.data_bit.",address))==task_aw2::cacheable(full,address,false),"stale data bitmap");
    require(full.get("hidden.yield")==0 && full.get("hidden.cpu_poll")<=1,"pending yield/unclassified poll mode");
    require(full.get("scheduler.round_epoch") && full.get("scheduler.planned_target")==full.get("slot9.target") &&
            full.get("scheduler.next_event")>(task_aw2::entry_cycle+64)/2,"scheduler target/event provenance");
    const auto next=std::min({task_aw2::periodic_next(full.get("system_timestamp")),full.get("card.deadline"),
        full.get("spi.deadline"),full.get("auxspi.deadline"),full.get("sqrt.deadline"),
        full.get("wifi.deadline"),full.get("div.deadline")});
    require(full.get("scheduler.next_event")==next,"scheduler event changed since target selection");
    require(full.get("service.powered_off")==0 && full.get("service.firmware_dirty")==0,"pending power/persistence service");
    require(full.get("service.rtc_processed")==full.get("service.rtc_due") &&
            full.get("service.display_last")==full.get("system_timestamp"),"unclassified periodic catch-up phase");
    require(full.get("service.spu_mixes")==full.get("system_timestamp")/1024 &&
            full.get("service.gpu_debt")==0,"SPU catch-up or GPU service ready");
    require(full.get("service.irq_cache9")==((full.get("irq9.ime")&1) ? (full.get("irq9.ie")&full.get("irq9.if")) : 0),
            "actual IRQ acceptance cache mismatch");
    require(full.get("service.irq_cache7")==((full.get("irq7.ime")&1) ? (full.get("irq7.ie")&full.get("irq7.if")) : 0),
            "actual ARM7 IRQ acceptance cache mismatch");
#if defined(AW4_ROMFREE_CERTIFICATION)
    task_aw2::preflight(core_projection(full),authority);
#else
    task_aw2::preflight(core_projection(full));
#endif
}
inline void seal(const Snapshot& snapshot) {
    require(!bound,"duplicate immutable seal");
    task_aw3::entry_preflight(snapshot);
    immutable=snapshot;
    immutable_digest=task_aw2::digest(snapshot);
    bound=true;
}
inline void verify_seal(const Snapshot& snapshot) {
    require(bound && snapshot==immutable && task_aw2::digest(snapshot)==immutable_digest,
            "stale/mutated immutable observation");
    task_aw3::entry_preflight(snapshot);
}
template<class Guards> inline void guarded_handoff(Guards guards) {
    if (!armed) { guards(); return; }
    try {
        guards();
        auto observed=passive();
        task_aw2::audit_snapshot(output,observed);
        seal(observed);
        verify_seal(passive());
        audit_text("capture_only_terminal","AU guards preserved; no successor fetch/accounting/dispatch; AX denied");
        task_aw::dispose(output,73);
    } catch (const std::exception& error) { fail(error.what()); }
    catch (...) { fail("handoff exception"); }
}
inline void handoff() { guarded_handoff([] {}); }
}
