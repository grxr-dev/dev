#pragma once
#include "aw6/prefix.h"

namespace task_aw7 {
using task_aw2::require;
inline bool armed=false,owned=false;
inline std::unique_ptr<task_aw6::Ledger> ledger;
inline std::thread::id owner;
inline unsigned bus_calls=0;
inline bool access_active=false;
[[noreturn]] inline void fail(const std::string& reason) noexcept { task_aw3::fail("AW7: "+reason); }
inline bool waiting() { return armed && !owned; }
inline bool owns() { return armed && owned; }
inline void arm_diagnostic() {
#if defined(AW7_DIAGNOSTIC_HARNESS)
    require(task_aw3::armed && task_aw3::output && !armed && !task_aw::observer,"AW7 exclusive diagnostic ownership");
    owner=std::this_thread::get_id();
    armed=true;
#else
    throw std::runtime_error("AW7 is not dynamically certified or armed in normal runner builds");
#endif
}
inline void receive(const task_aw::Event& event) {
    try {
        require(owns() && ledger && owner==std::this_thread::get_id(),"observer owner/thread");
        const auto state=task_aw3::passive();
        task_aw2::audit_snapshot(task_aw3::output,state);
        task_aw2::Observation actual{event.kind,event.pc,event.address,event.width,event.value,event.write,state};
        const auto index=ledger->cursor;
        const auto previous=ledger->previous;
        const bool accepted=ledger->accept(actual,previous);
        std::fprintf(task_aw3::output,"{\"event\":\"observation\",\"index\":%zu,\"kind\":%u,\"pc\":%u,\"address\":%u,\"width\":%u,\"value\":%u,\"write\":%s,\"accepted\":%s,\"previous\":\"%s\",\"chain\":\"%s\"}\n",
            index,unsigned(event.kind),event.pc,event.address,event.width,event.value,event.write ? "true" : "false",accepted ? "true" : "false",previous.c_str(),ledger->previous.c_str());
        require(!std::ferror(task_aw3::output),"audit write");
        if (!accepted) fail(ledger->failure);
        if (ledger->complete()) {
            require(!access_active && bus_calls==18 && state.get("cycle9")==3416875777 &&
                task_aw2::digest(state)=="ca5a376e0b5c0b70ed2dccc9155c7ba2a28332513fe27ee0cff8c52b013a6526","terminal bus/cycle/digest");
            task_aw3::audit_text("terminal","AW7 reduced owner complete; before forbidden fetch/account/dispatch and scheduler tail");
            task_aw::dispose(task_aw3::output,73);
        }
    } catch (const std::exception& error) { fail(error.what()); }
    catch (...) { fail("observer exception"); }
}
inline void handoff() {
    try {
        require(waiting() && task_aw3::armed && task_aw3::output && !task_aw::observer &&
            owner==std::this_thread::get_id(),"handoff ownership");
        const auto observed=task_aw3::passive();
        task_aw2::audit_snapshot(task_aw3::output,observed);
        ledger=std::make_unique<task_aw6::Ledger>(observed);
        require(task_aw3::passive()==observed,"torn actual provider binding");
        std::fprintf(task_aw3::output,"{\"event\":\"entry\",\"sha256\":\"%s\",\"events\":69}\n",task_aw2::digest(observed).c_str());
        owned=true;
        task_aw::observer=receive;
        task_aw::audit=task_aw3::output;
        task_aw::emit(task_aw::Kind::instruction,0x02001980);
    } catch (const std::exception& error) { fail(error.what()); }
    catch (...) { fail("handoff exception"); }
}
inline void validate_access(uint32_t pc,uint32_t address,unsigned width,uint32_t value,bool write) {
    require(owns() && ledger && task_aw::observer==receive && owner==std::this_thread::get_id() && !access_active,"access ownership");
    require(ledger->cursor<ledger->plan->size(),"extra access");
    const auto& next=(*ledger->plan)[ledger->cursor];
    require(next.kind==task_aw::Kind::access_before && next.pc==pc && next.address==address &&
        next.width==width && next.write==write && next.value==(write ? value : 0),"wrong/reordered access before underlying bus");
    require(pc!=task_aw6::stop_pc && !(address>=0x04000000 && !write),"forbidden status fetch/MMIO read");
}
template<bool Model,class Action> inline uint32_t access(uint32_t pc,uint32_t address,unsigned width,uint32_t value,bool write,Action action) {
    try {
        validate_access(pc,address,width,value,write);
        task_aw::emit(task_aw::Kind::access_before,pc,address,width,write ? value : 0,write);
        access_active=true;
        if constexpr (!Model) fail("runtime bus interlock remains closed pending actual-provider certification");
#if !defined(AW7_ROMFREE_MODEL)
        if constexpr (Model) fail("model bus unavailable outside ROM-free test executable");
#endif
        const auto result=uint32_t(action());
        access_active=false;
        ++bus_calls;
        task_aw::emit(task_aw::Kind::access_after,pc,address,width,write ? value : result,write);
        return result;
    } catch (const std::exception& error) { fail(error.what()); }
    catch (...) { fail("access exception"); }
}
template<class Action> inline uint32_t runtime_access(uint32_t pc,uint32_t address,unsigned width,uint32_t value,bool write,Action action) {
    return access<false>(pc,address,width,value,write,action);
}
inline void check_dispatch() {
    if (!owns()) return;
    try {
        require(task_aw::observer==receive && ledger && ledger->cursor && owner==std::this_thread::get_id(),"dispatch owner");
        const auto& previous=(*ledger->plan)[ledger->cursor-1];
        require(previous.kind==task_aw::Kind::instruction,"unobserved dispatch");
        const auto state=task_aw3::passive();
        require(state==previous.state,"provider changed between prospective guard and dispatch");
        task_aw6::guard_next(state,ledger->instructions-1);
    } catch (const std::exception& error) { fail(error.what()); }
}
}
