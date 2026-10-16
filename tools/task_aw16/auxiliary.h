#pragma once
#include "aw12/gpu.h"

namespace task_aw16 {
using task_aw2::Snapshot;
using task_aw2::require;
void overlay_aux(Snapshot&);
void wifi_aux(Snapshot&);
void trace_aux(Snapshot&);
void scheduler_aux(Snapshot&);
inline void aux_schema(const Snapshot& state) {
    std::map<std::string,uint8_t> expected={
        {"aux.schema",2},{"journal.bound",1},{"overlay.enabled",1},{"wifi.network_enabled",1},
        {"wifi.bridge",1},{"wifi.device",1},{"wifi.worker",1},{"wifi.scheduled",1},
        {"wifi.raw_deadline",8},{"wifi.timestamp",8},{"trace.count",8},
        {"trace.last.count",8},{"trace.last.cycle",8},{"trace.last.before",4},
        {"trace.last.after",4},{"trace.last.debt_before",4},{"trace.last.debt_after",4},
        {"scheduler.modulus",8},{"scheduler.sample",1}};
    require(state.fields.size()==expected.size() && state.hashes.empty(),"AW16 complete auxiliary schema");
    for (const auto& item:expected) {
        const auto found=state.fields.find(item.first);
        require(found!=state.fields.end() && found->second.width==item.second,"AW16 auxiliary field/width: "+item.first);
        if (item.second==1) require(found->second.value<=1,"AW16 auxiliary boolean");
    }
    require(state.get("aux.schema")==1,"AW16 auxiliary version");
    task_aw2::canonical(state);
}
inline Snapshot auxiliary() {
    Snapshot state; state.put("aux.schema",2,1);
    state.put("journal.bound",1,task_aw3::bound);
    overlay_aux(state); wifi_aux(state); trace_aux(state); scheduler_aux(state);
    aux_schema(state); return state;
}
inline void aux_admit(const Snapshot& state,const Snapshot& core) {
    aux_schema(state);
    require(!state.get("journal.bound"),"AW16 immutable AU seal forbids a new cap epoch");
    require(!state.get("overlay.enabled"),"AW16 overlay publication path enabled");
    require(!state.get("wifi.network_enabled") && !state.get("wifi.worker"),"AW16 asynchronous network work");
    require(!state.get("wifi.scheduled") && core.get("wifi.deadline")==UINT64_MAX,"AW16 Wifi event readiness");
    require(!state.get("scheduler.modulus") && !state.get("scheduler.sample"),"AW16 unclassified profiling branch");
    require(state.get("wifi.bridge") || (!state.get("wifi.device") && !state.get("wifi.worker") &&
        !state.get("wifi.timestamp") && !state.get("wifi.raw_deadline")),"AW16 absent bridge fields");
    require(state.get("wifi.timestamp")<=(core.get("cycle9")>>1),"AW16 Wifi time rewind");
    require(state.get("trace.count")<UINT64_MAX && state.get("trace.last.count")==state.get("trace.count"),"AW16 trace ordinal/provenance");
    if (!state.get("trace.count")) {
        for (const auto* key:{"trace.last.cycle","trace.last.before","trace.last.after","trace.last.debt_before","trace.last.debt_after"})
            require(!state.get(key),"AW16 empty trace record");
    }
}
}
