#pragma once
#include "canonical.h"
#include "state.h"
#include "savestate.h"

namespace task_aw2 {
inline Snapshot observed_timing() {
    NdsCp15SaveState copied{};
    cp15_savestate_export(&copied);
    Snapshot result;
    result.put("cp15.control",4,copied.visible.control);
    result.put("cp15.dcache",4,copied.cache_cfg[0]);
    result.put("cp15.icache",4,copied.cache_cfg[1]);
    result.put("cp15.generation",4,copied.timing_generation);
    for (unsigned index=0;index<8;++index)
        result.put("cp15.region."+std::to_string(index),4,copied.mpu_region[index]);
    result.put("itcm.enabled",1,copied.visible.itcm_enable);
    result.put("itcm.base",4,0);
    result.put("itcm.size",8,copied.visible.itcm_size);
    result.put("dtcm_map.enabled",1,copied.visible.dtcm_enable);
    result.put("dtcm_map.base",4,copied.visible.dtcm_base);
    result.put("dtcm_map.size",8,copied.visible.dtcm_size);
    const auto published=g_arm9_code_pub_gen;
    require(g_arm9_code_class_shift<=24 && !(g_arm9_code_class_shift&7), "unknown published class");
    result.put("timing.class",4,g_arm9_code_class_shift/8);
    result.put("timing.valid",1,published!=0);
    result.put("timing.generation",4,published);
    result.put("timing.publication",4,published);
    return result;
}
}
