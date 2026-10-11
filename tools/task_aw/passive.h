#pragma once
#include "task_aw_bridge.h"
#include "state.h"
#include "savestate.h"

namespace task_aw {
void runtime_snapshot(Snapshot&);
void scheduler_snapshot(Snapshot&);
void bus_snapshot(Snapshot&);
void io_snapshot(Snapshot&);
inline Snapshot passive_snapshot() {
    Snapshot out;
    out.values["schema"]=1;
    scheduler_snapshot(out);
    if (out.values.at("owner_thread")!=1) return out;
    out.copy("cpu",g_cpu);
    runtime_snapshot(out);
    bus_snapshot(out);
    io_snapshot(out);
    NdsCp15SaveState cp15{};
    cp15_savestate_export(&cp15);
    out.copy("cp15",cp15);
    return out;
}
}
