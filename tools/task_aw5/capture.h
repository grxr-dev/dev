#pragma once
#include "aw4/reconcile.h"

namespace task_aw5 {
inline bool selected() {
    const char* value=std::getenv("NDS_TASK_AW5_CAPTURE_ONLY");
    return value && std::string(value)=="1";
}
[[noreturn]] inline void handoff() {
    using task_aw2::require;
    try {
        require(selected() && task_aw3::armed,"AW5 capture ownership missing");
        task_aw3::audit_text("aw5_handoff","all AU guards passed; before successor accounting/fetch/dispatch; AX denied");
        std::fprintf(task_aw3::output,"{\"event\":\"journal_entry\",\"epoch\":%llu,\"serial\":%llu,\"records\":%zu}\n",
            static_cast<unsigned long long>(task_aw3::epoch),static_cast<unsigned long long>(task_aw3::serial),task_aw3::history.size());
        for (const auto& record:task_aw3::history)
            std::fprintf(task_aw3::output,"{\"event\":\"cap_record\",\"epoch\":%llu,\"serial\":%llu,\"cycle\":%llu,\"before\":%llu,\"after\":%llu,\"deadline\":%llu,\"cpu\":%u,\"source\":%u}\n",
                static_cast<unsigned long long>(record.epoch),static_cast<unsigned long long>(record.serial),
                static_cast<unsigned long long>(record.cycle),static_cast<unsigned long long>(record.before),
                static_cast<unsigned long long>(record.after),static_cast<unsigned long long>(record.deadline),record.cpu,record.source);
        task_aw3::audit_text("journal_sticky",task_aw3::sticky);
        const auto observed=task_aw3::passive();
        task_aw2::audit_snapshot(task_aw3::output,observed);
        task_aw4::entry(observed,task_aw2::au_manifest());
        const auto plan=task_aw4::expected(observed,task_aw2::au_manifest());
        require(plan.size()==77,"AW4 prospective projection incomplete");
        task_aw3::seal(observed);
        const auto repeated=task_aw3::passive();
        task_aw2::audit_snapshot(task_aw3::output,repeated);
        task_aw3::verify_seal(repeated);
        task_aw3::audit_text("aw5_capture_terminal","AW4 admission and pure 77-observation projection pass; no controller installed; no AX dispatch; nonreturning disposal");
        require(std::ferror(task_aw3::output)==0,"AW5 audit write failure");
        task_aw::dispose(task_aw3::output,73);
    } catch (const std::exception& error) { task_aw3::fail(error.what()); }
    catch (...) { task_aw3::fail("AW5 capture exception"); }
}
}
