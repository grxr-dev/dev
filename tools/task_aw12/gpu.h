#pragma once
#include "aw3/bridge.h"

namespace task_aw12 {
using task_aw2::Snapshot;
using task_aw2::require;
template<class Queue> inline void queue_snapshot(Snapshot& out,const char* name,const Queue& queue,unsigned limit) {
    const auto count=queue.Level();
    require(count<=limit && queue.IsEmpty()==(count==0),"GPU queue bounds/empty consistency");
    const std::string prefix=std::string("gpu.")+name+".";
    out.put(prefix+"count",4,count);
    for (unsigned index=0;index<count;++index) {
        const auto entry=queue.Peek(index);
        const auto item=prefix+std::to_string(index)+".";
        out.put(item+"command",1,entry.Command);
        out.put(item+"parameter",4,entry.Param);
    }
}
template<class Device> inline Snapshot gpu_project(const Device& device,uint64_t arm9_timestamp,unsigned shift) {
    Snapshot out;
    out.put("gpu.schema",2,1);
    out.put("gpu.geometry",1,device.GeometryEnabled);
    out.put("gpu.flush",4,device.FlushRequest);
    out.put("gpu.stat",4,device.GXStat);
    out.put("gpu.cycles",4,uint32_t(device.CycleCount));
    out.put("gpu.timestamp",8,device.Timestamp);
    out.put("gpu.arm9_timestamp",8,arm9_timestamp);
    out.put("gpu.clock_shift",1,shift);
    out.put("gpu.vertex_pipeline",4,uint32_t(device.VertexPipeline));
    out.put("gpu.normal_pipeline",4,uint32_t(device.NormalPipeline));
    out.put("gpu.polygon_pipeline",4,uint32_t(device.PolygonPipeline));
    out.put("gpu.vertex_slot_counter",4,uint32_t(device.VertexSlotCounter));
    out.put("gpu.vertex_slots_free",4,device.VertexSlotsFree);
    out.put("gpu.push_pop",4,device.NumPushPopCommands);
    out.put("gpu.tests",4,device.NumTestCommands);
    out.put("gpu.exec_parameters",4,device.ExecParamCount);
    queue_snapshot(out,"pipe",device.CmdPIPE,4);
    queue_snapshot(out,"fifo",device.CmdFIFO,256);
    queue_snapshot(out,"stall",device.CmdStallQueue,64);
    return out;
}
inline int64_t signed_word(uint64_t value) {
    require(value<=UINT32_MAX,"GPU signed-word width");
    return value&0x80000000 ? int64_t(value)-0x100000000LL : int64_t(value);
}
inline void gpu_schema(const Snapshot& state) {
    std::map<std::string,uint8_t> expected;
    expected["gpu.schema"]=2;
    for (const auto* key:{"gpu.geometry","gpu.clock_shift"}) expected[key]=1;
    for (const auto* key:{"gpu.flush","gpu.stat","gpu.cycles","gpu.vertex_pipeline","gpu.normal_pipeline",
        "gpu.polygon_pipeline","gpu.vertex_slot_counter","gpu.vertex_slots_free","gpu.push_pop","gpu.tests","gpu.exec_parameters"}) expected[key]=4;
    for (const auto* key:{"gpu.timestamp","gpu.arm9_timestamp"}) expected[key]=8;
    for (const auto& item:std::vector<std::pair<std::string,unsigned>>{{"pipe",4},{"fifo",256},{"stall",64}}) {
        const auto prefix="gpu."+item.first+".";
        const auto count=state.get(prefix+"count");
        require(count<=item.second,"GPU queue count"); expected[prefix+"count"]=4;
        for (unsigned index=0;index<count;++index) {
            const auto entry=prefix+std::to_string(index)+".";
            expected[entry+"command"]=1; expected[entry+"parameter"]=4;
        }
    }
    require(state.fields.size()==expected.size() && state.hashes.empty(),"GPU complete schema");
    for (const auto& item:expected) {
        const auto found=state.fields.find(item.first);
        require(found!=state.fields.end() && found->second.width==item.second,"GPU field/width: "+item.first);
    }
    require(state.get("gpu.schema")==1 && state.get("gpu.geometry")<=1 && state.get("gpu.clock_shift")==1 &&
        state.get("gpu.exec_parameters")<=32,"GPU version/classification");
    task_aw2::canonical(state);
}
inline bool gpu_work(const Snapshot& state) {
    gpu_schema(state);
    return state.get("gpu.geometry") && !state.get("gpu.flush") &&
        (state.get("gpu.pipe.count") || (state.get("gpu.stat")&(1u<<27)));
}
inline void gpu_admit(const Snapshot& state,const Snapshot& core) {
    gpu_schema(state);
    const auto raw=signed_word(state.get("gpu.cycles"));
    require(uint64_t(raw>0 ? raw : 0)==core.get("service.gpu_debt"),"GPU debt/source mismatch");
    require(!gpu_work(state),"GPU command/work eligible");
    for (const auto* name:{"gpu.pipe.count","gpu.fifo.count","gpu.stall.count","gpu.vertex_pipeline",
        "gpu.normal_pipeline","gpu.polygon_pipeline","gpu.push_pop","gpu.tests","gpu.exec_parameters"})
        require(state.get(name)==0,"GPU latent work: "+std::string(name));
    require(raw<=0 && !(state.get("gpu.stat")&(1u<<27)),"GPU pipeline debt/busy");
    require(state.get("gpu.timestamp")<=(core.get("cycle9")>>1) &&
        state.get("gpu.arm9_timestamp")<=core.get("cycle9"),"GPU clock ahead");
}
}
