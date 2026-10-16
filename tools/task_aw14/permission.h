#pragma once
#if !defined(AW14_LIVE_ONCE) || !defined(AW7_DIAGNOSTIC_HARNESS) || !defined(AW12_DIAGNOSTIC_CAPTURE_ONLY) || defined(AW9_LIVE_ONCE) || defined(AW7_ROMFREE_MODEL) || defined(AW8_ROMFREE_FIXTURE)
#error AW14 requires a fresh isolated one-shot capture build, never AW9 or fixture permission
#endif
#include <fstream>
#include "aw12/controller.h"
#include "aw7/integration.h"
#include "aw14_contract.h"

namespace task_aw14 {
inline bool initialized=false,consumed=false;
inline std::thread::id owner;
inline bool selected() {
    const char* value=std::getenv("NDS_TASK_AW14_ONCE");
    return value && std::string(value)=="1";
}
inline void prepare() {
    if (!selected()) return;
    try {
        using task_aw2::require;
        if (initialized) {
            require(owner==std::this_thread::get_id() && task_aw12::current,"AW14 scheduler owner changed");
            return;
        }
        require(!consumed && task_aw3::armed && task_aw3::output && !task_aw::observer &&
            task_aw3::owner==std::this_thread::get_id() && !task_aw12::current && !task_aw12::spent,
            "AW14 initial ownership");
        const char* path=std::getenv("NDS_TASK_AW14_PERMIT");
        require(path && *path,"AW14 fresh permit missing");
        std::ifstream input(path); std::string certificate,entry,nonce,extra;
        input>>certificate>>entry>>nonce;
        require(certificate==contract_identity && entry==task_aw6::entry_identity && nonce.size()==32 &&
            nonce.find_first_not_of("0123456789abcdef")==std::string::npos && !(input>>extra),"AW14 permit identity");
        auto* claim=task_aw3::exclusive_audit((std::string(path)+".claimed").c_str());
        require(claim,"AW14 permit already consumed or unwritable");
        std::fprintf(claim,"%s\n",nonce.c_str());
        require(std::fflush(claim)==0 && std::fclose(claim)==0,"AW14 permit claim flush/close");
        owner=std::this_thread::get_id();
        task_aw12::arm_capture_only(task_aw3::output);
        initialized=true;
        task_aw3::audit_text("aw14_capture_armed",contract_identity);
    } catch (const std::exception& error) { task_aw3::fail(std::string("AW14 preparation: ")+error.what()); }
    catch (...) { task_aw3::fail("AW14 preparation exception"); }
}
inline task_aw2::Snapshot expected_entry() {
    const char* path=std::getenv("NDS_TASK_AW14_EXPECTED");
    task_aw2::require(path && *path,"AW14 immutable comparison metadata missing");
    std::ifstream input(path); std::string hex,extra; input>>hex;
    task_aw2::require(!hex.empty() && hex.size()<1048576 && hex.size()%2==0 &&
        hex.find_first_not_of("0123456789abcdef")==std::string::npos && !(input>>extra),"AW14 comparison encoding");
    std::vector<uint8_t> bytes;
    for (size_t index=0;index<hex.size();index+=2) bytes.push_back(uint8_t(std::stoul(hex.substr(index,2),nullptr,16)));
    auto state=task_aw2::decode(bytes);
    task_aw2::require(task_aw2::canonical(state)==bytes && task_aw2::digest(state)==task_aw6::entry_identity,"AW14 comparison identity");
    return state;
}
inline void handoff() {
    try {
        using task_aw2::require;
        require(selected() && initialized && !consumed && owner==std::this_thread::get_id() &&
            task_aw3::armed && task_aw3::output && !task_aw::observer && !task_aw7::owns() &&
            !task_aw7::runtime_authorized && task_aw12::current && !task_aw12::spent,"AW14 one-shot handoff ownership");
        consumed=true;
        const auto expected=expected_entry();
        const auto actual=task_aw3::passive();
        task_aw3::audit_text("aw14_live_preflight","all original AU guards passed; no candidate accounting/fetch/dispatch yet");
        task_aw2::audit_snapshot(task_aw3::output,actual);
        task_aw6::entry(actual);
        require(actual==expected,"AW14 complete original-provider entry comparison");
        task_aw3::audit_text("aw14_preflight_accepted",task_aw2::digest(actual));
        task_aw7::arm_diagnostic();
        task_aw7::handoff();
        require(task_aw7::owns() && task_aw7::ledger && task_aw7::ledger->cursor==1,"AW14 reduced owner transfer");
        task_aw7::runtime_authorized=true;
        task_aw3::audit_text("aw14_runtime_permission","one exact 11-instruction prerequisite prefix, then unchanged AW12 capture-only fence; B4 forbidden");
    } catch (const std::exception& error) { task_aw3::fail(std::string("AW14 handoff: ")+error.what()); }
    catch (...) { task_aw3::fail("AW14 handoff exception"); }
}
}
