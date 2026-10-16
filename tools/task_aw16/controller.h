#pragma once
#include "aw7/integration.h"
#include "aw12/controller.h"
#include "plan.h"

namespace task_aw16 {
class Controller;
inline Controller* current=nullptr;
inline bool spent=false;
void observe(const task_aw::Event&);
#if defined(AW16_ROMFREE)
inline void (*test_fault)(const std::string&)=nullptr;
inline bool (*test_skip)(const std::string&)=nullptr;
#endif
class Controller {
    FILE* output;
    std::thread::id owner=std::this_thread::get_id();
    std::vector<Step> plan;
    size_t cursor=0;
    bool started=false;
    std::string previous,ledger_chain,predecessor_chain;
    Snapshot predecessor_seal;
    uint64_t ticket=0,frame=0;
    [[noreturn]] void stop(bool success,const std::string& reason) noexcept {
        task_aw3::audit_text(success ? "aw16_terminal" : "aw16_failure",reason);
        if (output) std::fprintf(output,"{\"event\":\"aw16_disposal\",\"success\":%s,\"stages\":%zu,\"chain\":\"%s\",\"guest\":0,\"MMIO\":0}\n",
            success ? "true" : "false",cursor,previous.c_str());
        task_aw::dispose(output,success ? 73 : 79);
    }
    void ancestry(bool transferred) {
        require(owner==std::this_thread::get_id() && output && output==task_aw3::output && task_aw3::armed,"AW16 owner/thread/audit");
        require(current==this && (!transferred || spent),"AW16 successor ownership/spent latch");
        auto* ancestor=task_aw12::current;
        require(ancestor && task_aw12::spent && !task_aw12::frame && !task_aw12::runtime_saved_unwind(),"AW16 predecessor ownership");
        require(ancestor->phase==(transferred ? task_aw12::Phase::transferred : task_aw12::Phase::admitted) &&
            ancestor->cursor==8 && ancestor->ticket==ticket && ancestor->bound_frame==frame && ancestor->previous==predecessor_chain &&
            ancestor->output==output && task_aw12::frame_serial==frame,"AW16 private predecessor receipt");
        require(task_aw12::ticket_serial==ticket,"AW16 predecessor ticket epoch");
        require(task_aw7::owns() && task_aw7::ledger && task_aw7::owner==owner && !task_aw7::access_active &&
            task_aw7::bus_calls==18 && task_aw7::ledger->complete() && task_aw7::ledger->previous==ledger_chain,
            "AW16 completed ledger receipt changed");
        require(task_aw7::ledger->seal==predecessor_seal,"AW16 immutable predecessor seal changed");
        std::string identity=task_aw6::entry_identity;
        for (size_t index=0;index<task_aw7::ledger->plan->size();++index)
            identity=task_aw4::chain(identity,index,(*task_aw7::ledger->plan)[index]);
        require(identity==ledger_chain,"AW16 logical predecessor plan seal changed");
        require(task_aw::observer==(transferred ? observe : task_aw7::receive) && task_aw::audit==output,"AW16 observer ownership");
    }
    void accept(const std::string& label,bool observed,task_aw::Kind kind) {
        try {
            ancestry(true);
            require(started && cursor<plan.size(),"AW16 missing/extra/spent phase");
            const auto& expected=plan[cursor];
            require(label==expected.label && observed==expected.observed && (!observed || kind==expected.kind),"AW16 missing/duplicate/reordered/unexpected event");
            const auto core=task_aw3::passive(),gpu=task_aw12::runtime_gpu_observation(),extra=auxiliary();
            require(task_aw3::passive()==core && task_aw12::runtime_gpu_observation()==gpu && auxiliary()==extra,"AW16 torn passive observation");
            require(core==expected.core && gpu==expected.gpu && extra==expected.extra,"AW16 full core/GPU/auxiliary transition");
            task_aw4::journal_valid(core); aux_schema(extra); task_aw12::gpu_schema(gpu);
            auto bytes=task_aw2::canonical(core);
            bytes.insert(bytes.begin(),previous.begin(),previous.end());
            for (const auto& extension:{gpu,extra}) {
                const auto data=task_aw2::canonical(extension); bytes.insert(bytes.end(),data.begin(),data.end());
            }
            task_aw2::little(bytes,cursor,8); task_aw2::little(bytes,observed,1);
            task_aw2::little(bytes,observed ? unsigned(kind) : 0,1); task_aw2::string_bytes(bytes,label);
            const auto chain=brainage_custom::resource_detail::sha256(bytes.data(),bytes.size());
            task_aw2::audit_snapshot(output,core);
            for (const auto& extension:std::vector<std::pair<const char*,Snapshot>>{{"gpu",gpu},{"auxiliary",extra}}) {
                const auto data=task_aw2::canonical(extension.second);
                std::fprintf(output,"{\"event\":\"aw16_%s\",\"sha256\":\"%s\",\"canonical_hex\":\"",extension.first,task_aw2::digest(extension.second).c_str());
                for (auto byte:data) std::fprintf(output,"%02x",unsigned(byte));
                std::fputs("\"}\n",output);
            }
            std::fprintf(output,"{\"event\":\"aw16_stage\",\"index\":%zu,\"label\":\"%s\",\"observed\":%s,\"kind\":%u,\"previous\":\"%s\",\"chain\":\"%s\"}\n",cursor,label.c_str(),observed ? "true" : "false",observed ? unsigned(kind) : 0,previous.c_str(),chain.c_str());
            require(!std::ferror(output),"AW16 audit write"); previous=chain; ++cursor;
            if (cursor==plan.size()) stop(true,"AW16 new slice established; dispose before guest fetch/account/dispatch");
        } catch (const std::exception& error) { stop(false,error.what()); }
        catch (...) { stop(false,"AW16 transition exception"); }
    }
public:
    explicit Controller(FILE* file):output(file) {}
    bool active() const { return started; }
    [[noreturn]] void fail(const std::string& reason) noexcept { stop(false,reason); }
    void begin(FILE* file,const Snapshot& core,const Snapshot& gpu,uint64_t receipt_ticket,
               uint64_t receipt_frame,uint64_t events,const std::string& chain) {
        try {
            require(!started && !spent && file==output && events==8 && receipt_ticket==1 && receipt_frame==566 &&
                chain=="10bad78f6ef2fd96a21b26be7e074943e6ded5fa5541844c731d3e39892472b4","AW16 exact one-use AW14 predecessor");
            ticket=receipt_ticket; frame=receipt_frame; predecessor_chain=chain;
            require(task_aw7::ledger && task_aw2::digest(task_aw7::ledger->plan->front().state)==task_aw6::entry_identity,"AW16 prefix entry seal");
            task_aw6::Ledger expected(task_aw7::ledger->plan->front().state);
            for (const auto& event:*expected.plan) require(expected.accept(event,expected.previous),"AW16 predecessor model receipt");
            require(expected.complete() && task_aw7::ledger->plan->size()==expected.plan->size(),"AW16 predecessor completeness");
            for (size_t index=0;index<expected.plan->size();++index)
                require(task_aw2::same((*task_aw7::ledger->plan)[index],(*expected.plan)[index]),"AW16 predecessor plan altered");
            ledger_chain=expected.previous; predecessor_seal=expected.seal; ancestry(false);
            const auto extra=auxiliary();
            require(auxiliary()==extra && task_aw3::passive()==core && task_aw12::runtime_gpu_observation()==gpu,"AW16 repeat entry samples");
            plan=tail_plan(core,gpu,extra);
            previous=chain;
            std::fprintf(output,"{\"event\":\"aw16_entry_seal\",\"predecessor\":\"%s\",\"ledger\":\"%s\",\"auxiliary\":\"%s\",\"ticket\":%llu,\"frame\":%llu}\n",
                chain.c_str(),ledger_chain.c_str(),task_aw2::digest(extra).c_str(),static_cast<unsigned long long>(ticket),static_cast<unsigned long long>(frame));
            spent=true; started=true;
            task_aw12::current->phase=task_aw12::Phase::transferred;
            task_aw::observer=observe;
            mark("successor_admitted");
        } catch (const std::exception& error) { stop(false,error.what()); }
        catch (...) { stop(false,"AW16 admission exception"); }
    }
    void point(const std::string& label) { accept(label,false,task_aw::Kind::device); }
    void event(const task_aw::Event& event) {
        if (!started || cursor>=plan.size()) fail("AW16 event before admission/after terminal");
        const auto& expected=plan[cursor];
        if (event.pc || event.address || event.width || event.value || event.write) fail("AW16 unexpected guest/access payload");
        accept(expected.label,true,event.kind);
    }
};
inline void arm(FILE* output) {
#if defined(AW16_DIAGNOSTIC_TAIL)
    try {
        require(output && output==task_aw3::output && task_aw3::armed && task_aw3::owner==std::this_thread::get_id() && !current && !spent,"AW16 one-use diagnostic arm");
        static std::unique_ptr<Controller> controller;
        require(!controller,"AW16 arm reused"); controller=std::make_unique<Controller>(output); current=controller.get();
    } catch (const std::exception& error) {
        if (current) current->fail(error.what());
        task_aw3::fail(error.what());
    }
#else
    throw std::runtime_error("AW16 unavailable in default runtime");
#endif
}
inline bool receive_fence(FILE* output,const Snapshot& core,const Snapshot& gpu,uint64_t ticket,
                          uint64_t frame,uint64_t count,const std::string& chain) {
    if (!current && spent) task_aw3::fail("AW16 successor lost after consumption");
    if (!current) return false;
    current->begin(output,core,gpu,ticket,frame,count,chain); return true;
}
inline void observe(const task_aw::Event& event) {
    if (!current) task_aw3::fail("AW16 observer without owner");
    auto* owner=current;
#if defined(AW16_ROMFREE)
    if (test_fault) test_fault("observer");
#endif
    owner->event(event);
}
inline void mark(const char* label) {
    if (!current && spent) task_aw3::fail("AW16 missing consumed successor");
    if (!current || !current->active()) return;
    auto* owner=current;
#if defined(AW16_ROMFREE)
    if (test_fault) test_fault(label);
    if (test_skip && test_skip(label)) return;
#endif
    owner->point(label);
}
inline void slice_gate(int cpu,uint32_t quantum) {
    if (!current || !current->active()) return;
    if ((cpu==1 && quantum==63)) mark("slice7_gate");
    else if (cpu==0 && quantum==49) mark("slice9_gate");
    else current->fail("AW16 unexpected CPU/quantum");
}
inline void slice_begun(int cpu,uint32_t quantum) {
    if (!current || !current->active()) return;
    if (cpu!=0 || quantum!=49) current->fail("AW16 unexpected slice begin");
    mark("slice_begun_stop");
    current->fail("AW16 terminal returned");
}
}
