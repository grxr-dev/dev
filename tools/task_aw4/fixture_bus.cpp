#include "bus.cpp"
#include "fixture.h"
namespace task_aw4::fixture {
void bus_begin() {
    g_main_ram.assign(0x400000,0); g_dtcm.assign(0x4000,0);
    const auto anchors=task_aw2::au_manifest();
    for (const auto& item:anchors.fields) {
        const auto point=item.first.find('.');
        const bool memory=item.first.rfind("code.",0)==0 || item.first.rfind("literal.",0)==0 || item.first.rfind("protected.",0)==0;
        if (!memory && item.first!="dtcm_stack_word") continue;
        const uint32_t address=memory ? std::stoul(item.first.substr(point+1),nullptr,16) : 0x027e3658;
        auto& bytes=address>=0x027e0000 ? g_dtcm : g_main_ram;
        const auto offset=address-(address>=0x027e0000 ? 0x027e0000u : 0x02000000u);
        for (unsigned index=0;index<item.second.width;++index) bytes.at(offset+index)=uint8_t(item.second.value>>(index*8));
    }
    NdsCp15SaveState copied{};
    cp15_savestate_export(&copied);
    copied.visible.control=0x1005; copied.visible.dtcm_enable=true; copied.visible.dtcm_base=0x027e0000;
    copied.visible.dtcm_size=0x4000; copied.visible.itcm_enable=false;
    copied.mpu_region[0]=0x0200002b; copied.mpu_region[1]=0x0400002f;
    copied.cache_cfg[0]=1; copied.cache_cfg[1]=1;
    std::string error;
    task_aw2::require(cp15_savestate_import(copied,&error),"real CP15 synthetic fixture import: "+error);
    runtime_code_cycles(0x0200197c); runtime_mem_cycles(0x020019a8,4,0);
}
void bus_mutate(const std::string& name) {
    if (name=="image") g_main_ram.at(0x80)^=1;
    else if (name=="code") g_main_ram.at(0x1980)^=1;
    else if (name=="dtcm") g_dtcm.at(0x80)^=1;
    else if (name=="latch") g_last_data_addr[0]^=4;
    else task_aw2::require(false,"unknown bus mutation");
}
}
