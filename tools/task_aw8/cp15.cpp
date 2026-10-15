#include "binding.h"
#include "aw8_cp15.cpp"
namespace task_aw8 {
void cp15_begin() {
    const auto& saved=entry();
    NdsCp15SaveState copied{};
    copied.visible.control=saved.get("cp15.control");
    copied.visible.high_vectors=bool(copied.visible.control&(1u<<13));
    copied.visible.itcm_enable=saved.get("itcm.enabled"); copied.visible.itcm_size=saved.get("itcm.size");
    copied.visible.dtcm_enable=saved.get("dtcm_map.enabled"); copied.visible.dtcm_base=saved.get("dtcm_map.base");
    copied.visible.dtcm_size=saved.get("dtcm_map.size"); copied.timing_generation=saved.get("cp15.generation");
    for (unsigned index=0;index<8;++index) {
        copied.mpu_region[index]=saved.get(task_aw2::numbered("cp15.region.",index));
        copied.access_perm[index]=saved.get(task_aw2::numbered("hidden.permission.",index));
    }
    copied.cache_cfg[0]=saved.get("cp15.dcache"); copied.cache_cfg[1]=saved.get("cp15.icache");
    std::string error;
    require(cp15_savestate_import(copied,&error),"synthetic CP15 import: "+error);
}
}
