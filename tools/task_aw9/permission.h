#pragma once
#if !defined(AW9_LIVE_ONCE) || !defined(AW7_DIAGNOSTIC_HARNESS) || defined(AW7_ROMFREE_MODEL) || defined(AW8_ROMFREE_FIXTURE)
#error AW9 is an isolated one-shot live diagnostic, never a fixture or gameplay mode
#endif
#include <fstream>
#include "aw7/integration.h"
namespace task_aw9 {
inline bool consumed=false;
inline bool selected() {
    const char* value=std::getenv("NDS_TASK_AW9_ONCE");
    return value && std::string(value)=="1";
}
inline std::string difference(const task_aw2::Snapshot& expected,const task_aw2::Snapshot& actual) {
    for (const auto& item:expected.fields) {
        const auto found=actual.fields.find(item.first);
        if (found==actual.fields.end()) return "missing scalar "+item.first;
        if (!(found->second==item.second)) return item.first+": expected "+std::to_string(item.second.value)+
            " (width "+std::to_string(item.second.width)+"), observed "+std::to_string(found->second.value)+
            " (width "+std::to_string(found->second.width)+")";
    }
    for (const auto& item:actual.fields) if (!expected.fields.count(item.first)) return "extra scalar "+item.first;
    for (const auto& item:expected.hashes) {
        const auto found=actual.hashes.find(item.first);
        if (found==actual.hashes.end()) return "missing identity "+item.first;
        if (found->second!=item.second) return item.first+": expected "+item.second+", observed "+found->second;
    }
    for (const auto& item:actual.hashes) if (!expected.hashes.count(item.first)) return "extra identity "+item.first;
    return "no logical snapshot difference; see predicate rejection";
}
inline task_aw2::Snapshot expected_entry() {
    const char* path=std::getenv("NDS_TASK_AW9_EXPECTED");
    task_aw2::require(path && *path,"AW9 immutable comparison metadata missing");
    std::ifstream input(path); std::string hex; input>>hex;
    task_aw2::require(!hex.empty() && hex.size()<1048576 && hex.size()%2==0 &&
        hex.find_first_not_of("0123456789abcdef")==std::string::npos,"AW9 comparison encoding");
    std::vector<uint8_t> bytes;
    for (size_t index=0;index<hex.size();index+=2) bytes.push_back(uint8_t(std::stoul(hex.substr(index,2),nullptr,16)));
    const auto expected=task_aw2::decode(bytes);
    task_aw2::require(task_aw2::canonical(expected)==bytes && task_aw2::digest(expected)==task_aw6::entry_identity,
        "AW9 comparison metadata identity");
    return expected;
}
inline void handoff() {
    try {
        using task_aw2::require;
        require(selected() && !consumed && task_aw3::armed && task_aw3::output && !task_aw::observer &&
            !task_aw7::owns() && !task_aw7::runtime_authorized,"AW9 one-shot ownership");
        consumed=true;
        const char* path=std::getenv("NDS_TASK_AW9_PERMIT");
        require(path && *path,"AW9 permit missing");
        std::ifstream input(path); std::string certificate,entry,nonce,extra;
        input>>certificate>>entry>>nonce;
        require(certificate=="8381e1335266a05767982f292eb5237eb157bb5d8d9ea431c1a81d7552bae417" &&
            entry==task_aw6::entry_identity && nonce.size()==32 && nonce.find_first_not_of("0123456789abcdef")==std::string::npos &&
            !(input>>extra),"AW9 permit identity");
        auto* claim=task_aw3::exclusive_audit((std::string(path)+".claimed").c_str());
        require(claim,"AW9 permit already consumed or unwritable");
        std::fprintf(claim,"%s\n",nonce.c_str());
        require(std::fflush(claim)==0 && std::fclose(claim)==0,"AW9 permit claim flush/close");
        const auto expected=expected_entry();
        const auto actual=task_aw3::passive();
        task_aw3::audit_text("aw9_live_preflight","all original AU guards passed; before candidate accounting/fetch/dispatch; original computed identities only");
        task_aw2::audit_snapshot(task_aw3::output,actual);
        try { task_aw6::entry(actual); }
        catch (const std::exception& error) {
            task_aw3::audit_text("aw9_first_mismatch",std::string(error.what())+"; first logical difference: "+difference(expected,actual));
            task_aw3::fail(std::string("AW9 preflight: ")+error.what());
        }
        require(actual==expected,"AW9 full comparison differs after exact admission");
        task_aw3::audit_text("aw9_preflight_accepted",task_aw2::digest(actual));
        task_aw7::arm_diagnostic();
        task_aw7::handoff();
        require(task_aw7::owns() && task_aw7::ledger && task_aw7::ledger->cursor==1,"AW9 reduced controller ownership transfer");
        task_aw7::runtime_authorized=true;
        task_aw3::audit_text("aw9_runtime_permission","one exact 11-instruction live prefix; all AW7 guards unchanged; no status read");
    } catch (const std::exception& error) { task_aw3::fail(std::string("AW9 handoff: ")+error.what()); }
    catch (...) { task_aw3::fail("AW9 handoff exception"); }
}
}
