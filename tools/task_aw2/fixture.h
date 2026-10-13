#pragma once
#include "model.h"

namespace task_aw2::synthetic {
inline Snapshot entry() {
    auto state=au_manifest();
    state.put("return_depth",4,2);
    state.put("cap.count",4,1);
    for (const auto& item:layout(state))
        if (!state.fields.count(item.first)) state.put(item.first,item.second,0);
    state.put("return.0",4,0x02067568);
    state.put("return.1",4,0x02001a20);
    for (const auto* key:{"owner_thread","round_active","force_tier3","arm7_started","timing.valid"})
        state.put(key,1,1);
    state.put("cp15.control",4,0x1005);
    state.put("cp15.region.0",4,0x0200002b);
    state.put("cp15.region.1",4,0x0400002f);
    state.put("cp15.dcache",4,1);
    state.put("cp15.icache",4,1);
    for (const auto* key:{"cp15.generation","timing.generation","timing.publication"}) state.put(key,4,9);
    state.put("timing.class",4,1);
    state.put("dtcm_map.enabled",1,1);
    state.put("dtcm_map.base",4,0x027e0000);
    state.put("dtcm_map.size",8,0x4000);
    const auto base=entry_cycle-9;
    state.put("system_timestamp",8,base>>1);
    state.put("slot9.cycle",8,base);
    state.put("slot9.target",8,base+128);
    state.put("slice_cap",8,base+128);
    state.put("fast_limit",8,base+128);
    state.put("cap.0.cycle",8,base);
    state.put("cap.0.base",8,base);
    state.put("cap.0.quantum",8,128);
    state.put("cap.0.after",8,base+128);
    state.put("snapshot_ordinal",8,state.get("ordinal9"));
    for (const auto* prefix:{"card", "spi", "auxspi", "sqrt", "wifi", "div"})
        state.put(std::string(prefix)+".deadline",8,UINT64_MAX);
    state.put("div.qlo",4,0x12345678);
    state.put("div.qhi",4,0x9abcdef0);
    state.put("div.rlo",4,0x87654321);
    state.put("div.rhi",4,0xdeadbeef);
    return state;
}
}
