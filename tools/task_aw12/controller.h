#pragma once
#include "aw6/prefix.h"
#include "gpu.h"

namespace task_aw12 {
enum class Phase : uint8_t { idle,requested,escaped,preserved,consumed,saved,fenced,admitted,disposed,failed };
using Source=Snapshot(*)();
using Saved=bool(*)();
inline constexpr const char* terminal_identity="ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526";
struct Frame;
inline Frame* frame=nullptr;
inline uint64_t frame_serial=0,ticket_serial=0;
inline bool spent=false;
inline unsigned frame_depth();
class Controller;
inline Controller* current=nullptr;

class Controller {
    FILE* output;
    Source core_source,gpu_source;
    Saved saved_source;
    const std::thread::id owner=std::this_thread::get_id();
    Snapshot entry;
    std::string previous;
    uint64_t cursor=0,ticket=0,bound_frame=0;
    Phase phase=Phase::idle;
    [[noreturn]] void stop(bool success,const std::string& reason) noexcept {
        phase=success ? Phase::disposed : Phase::failed;
        if (output) {
            std::fprintf(output,"{\"event\":\"%s\",\"reason\":\"",success ? "terminal" : "failure");
            for (unsigned char character:reason) {
                if (character=='"' || character=='\\') std::fputc('\\',output);
                if (character<32) std::fprintf(output,"\\u%04x",unsigned(character)); else std::fputc(character,output);
            }
            std::fprintf(output,"\",\"events\":%llu,\"ticket\":%llu,\"chain\":\"%s\",\"guest_instructions\":0,\"MMIO\":0}\n",
                static_cast<unsigned long long>(cursor),static_cast<unsigned long long>(ticket),previous.c_str());
        }
        task_aw::dispose(output,output && !std::ferror(output) ? success ? 73 : 79 : 78);
    }
    void check_owner() { require(owner==std::this_thread::get_id(),"AW12 thread ownership"); }
    Snapshot expected(bool yielded,bool slot_saved) const {
        auto state=entry;
        if (yielded) state.put("unwinding",1,1);
        if (slot_saved) state.put("slot9.cycle",8,entry.get("cycle9"));
        return state;
    }
    Snapshot sample(bool yielded,bool slot_saved) {
        check_owner();
        auto state=core_source();
        task_aw4::full_schema(state); task_aw4::journal_valid(state);
        require(state==expected(yielded,slot_saved),"AW12 full protected transition mismatch");
        return state;
    }
    void audit(const char* name,const Snapshot& state,const Snapshot& extra={}) {
        auto material=task_aw2::canonical(state);
        const auto extension=task_aw2::canonical(extra);
        material.insert(material.begin(),previous.begin(),previous.end());
        material.insert(material.end(),extension.begin(),extension.end());
        task_aw2::little(material,cursor,8); task_aw2::little(material,ticket,8);
        task_aw2::little(material,unsigned(phase),1);
        const bool saved=saved_source();
        const auto depth=frame_depth();
        task_aw2::little(material,saved,1); task_aw2::little(material,depth,4);
        task_aw2::little(material,bound_frame,8);
        const std::string label=name;
        task_aw2::string_bytes(material,label);
        const auto chain=brainage_custom::resource_detail::sha256(material.data(),material.size());
        task_aw2::audit_snapshot(output,state);
        if (!extra.fields.empty()) {
            const auto bytes=task_aw2::canonical(extra);
            std::fprintf(output,"{\"event\":\"gpu_snapshot\",\"sha256\":\"%s\",\"canonical_hex\":\"",task_aw2::digest(extra).c_str());
            for (auto byte:bytes) std::fprintf(output,"%02x",unsigned(byte));
            std::fputs("\"}\n",output);
        }
        std::fprintf(output,"{\"event\":\"%s\",\"index\":%llu,\"phase\":%u,\"ticket\":%llu,\"frame\":%llu,\"saved_valid\":%s,\"frame_depth\":%u,\"previous\":\"%s\",\"chain\":\"%s\"}\n",
            name,static_cast<unsigned long long>(cursor),unsigned(phase),static_cast<unsigned long long>(ticket),
            static_cast<unsigned long long>(bound_frame),saved ? "true" : "false",depth,previous.c_str(),chain.c_str());
        require(!std::ferror(output),"AW12 audit IO"); previous=chain; ++cursor;
    }
public:
    Controller(FILE* file,Source core,Source gpu,Saved saved):output(file),core_source(core),gpu_source(gpu),saved_source(saved) {}
    bool active() const { return phase!=Phase::idle; }
    [[noreturn]] void fail(const std::string& reason) noexcept { stop(false,reason); }
    void offer(const Snapshot& terminal);
    bool tier3_exit();
    void preserved();
    bool slice_exit(int cpu);
    void slice_saved(int cpu);
    void fence();
    void guest_attempt() { if (active()) fail("AW12 guest fetch/account/dispatch forbidden"); }
};
struct Frame {
    Frame* parent=nullptr;
    uint64_t serial=0;
    bool prior_static=false,prior_dispatch=false,tracking=false;
    Frame(bool actual_prior_static,bool actual_parent_dispatch) {
        if (!current) return;
        current->guest_attempt();
        parent=frame; prior_static=actual_prior_static; prior_dispatch=actual_parent_dispatch;
        if (frame_serial==UINT64_MAX) current->fail("AW12 frame ordinal overflow");
        serial=++frame_serial; tracking=true; frame=this;
    }
    ~Frame() {
        if (!tracking) return;
        if (frame!=this) current->fail("AW12 frame order");
        frame=parent;
    }
};
inline unsigned frame_depth() {
    unsigned count=0;
    for (auto* item=frame;item;item=item->parent) {
        require(++count<=64,"AW12 frame depth/cycle");
    }
    return count;
}
inline void Controller::offer(const Snapshot& terminal) {
    try {
        check_owner();
        require(phase==Phase::idle && !spent && output && core_source && gpu_source && saved_source,"AW12 one-use arming");
        require(frame && !frame->parent && !frame->prior_static && !frame->prior_dispatch,"AW12 requires outermost unguarded Tier-3 frame");
        task_aw4::full_schema(terminal); task_aw4::journal_valid(terminal);
        require(task_aw2::digest(terminal)==terminal_identity && !saved_source(),"AW12 terminal identity/unwind latch");
        task_aw6::ready_before(terminal,terminal.get("cycle9"));
        require(core_source()==terminal && core_source()==terminal,"AW12 torn terminal binding");
        entry=terminal;
        require(ticket_serial!=UINT64_MAX,"AW12 ticket overflow");
        ticket=++ticket_serial; bound_frame=frame->serial; spent=true;
        phase=Phase::requested; previous=terminal_identity;
        audit("yield_requested",terminal);
    } catch (const std::exception& error) { fail(error.what()); }
    catch (...) { fail("AW12 offer exception"); }
}
inline bool Controller::tier3_exit() {
    if (!active()) return false;
    try {
        require(phase==Phase::requested && frame && frame->serial==bound_frame && !saved_source(),"AW12 Tier-3 ownership/order");
        auto state=sample(false,false); phase=Phase::escaped; audit("tier3_exit",state); return true;
    } catch (const std::exception& error) { fail(error.what()); }
    catch (...) { fail("AW12 Tier-3 exception"); }
}
inline void Controller::preserved() {
    try {
        require(phase==Phase::escaped && frame && frame->serial==bound_frame && saved_source(),"AW12 preserved latch/order");
        auto state=sample(true,false); phase=Phase::preserved; audit("unwind_preserved",state);
    } catch (const std::exception& error) { fail(error.what()); }
    catch (...) { fail("AW12 preserve exception"); }
}
inline bool Controller::slice_exit(int cpu) {
    if (!active()) return false;
    try {
        require(phase==Phase::preserved && cpu==0 && !frame && !saved_source(),"AW12 slice consume/order");
        auto state=sample(true,false); phase=Phase::consumed; audit("slice_consumed",state); return true;
    } catch (const std::exception& error) { fail(error.what()); }
    catch (...) { fail("AW12 slice consume exception"); }
}
inline void Controller::slice_saved(int cpu) {
    if (!active()) return;
    try {
        require(phase==Phase::consumed && cpu==0 && !frame && !saved_source(),"AW12 slot-save order");
        auto state=sample(true,true); phase=Phase::saved; audit("slot_saved",state);
    } catch (const std::exception& error) { fail(error.what()); }
    catch (...) { fail("AW12 slot-save exception"); }
}
inline void Controller::fence() {
    if (!active()) return;
    try {
        require(phase==Phase::saved && !frame && !saved_source(),"AW12 pre-device fence missing/duplicate/order");
        auto state=sample(true,true); phase=Phase::fenced; audit("pre_device_fence",state);
        const auto gpu=gpu_source(); gpu_schema(gpu);
        require(gpu_source()==gpu && sample(true,true)==state,"AW12 torn passive GPU observation");
        audit("gpu_observed",state,gpu);
        gpu_admit(gpu,state);
        phase=Phase::admitted; audit("scheduler_admitted_capture_only",state,gpu);
        stop(true,"AW12 pre-device capture complete; no service/new slice/guest re-entry");
    } catch (const std::exception& error) { fail(error.what()); }
    catch (...) { fail("AW12 fence exception"); }
}
inline void install(Controller& controller) {
#if defined(AW12_DIAGNOSTIC_CAPTURE_ONLY)
    require(!current && !spent,"AW12 installation already owned/spent"); current=&controller;
#else
    throw std::runtime_error("AW12 unavailable in default build");
#endif
}
inline bool offer(const Snapshot& state) { if (!current) return false; current->offer(state); return true; }
inline bool tier3_exit() { return current ? current->tier3_exit() : false; }
inline void preserved() { if (current) current->preserved(); }
inline bool slice_exit(int cpu) { return current ? current->slice_exit(cpu) : false; }
inline void slice_saved(int cpu) { if (current) current->slice_saved(cpu); }
inline void pre_device_fence() { if (current) current->fence(); }
inline void guard_guest() { if (current) current->guest_attempt(); }
Snapshot runtime_gpu_observation();
bool runtime_saved_unwind();
inline void arm_capture_only(FILE* output) {
#if defined(AW12_DIAGNOSTIC_CAPTURE_ONLY)
    require(task_aw3::armed && task_aw3::owner==std::this_thread::get_id() && output &&
        output==task_aw3::output && !current && !spent,"AW12 exclusive runtime capture ownership");
    static std::unique_ptr<Controller> controller;
    require(!controller,"AW12 runtime arm is one-use");
    controller=std::make_unique<Controller>(output,task_aw3::passive,runtime_gpu_observation,runtime_saved_unwind);
    install(*controller);
#else
    throw std::runtime_error("AW12 unavailable in default build");
#endif
}
}
