#include "binding.h"
#include "aw8_bus.cpp"
namespace task_aw8 {
void bus_begin() {
    const auto& saved=entry();
    g_main_ram.assign(0x400000,0); g_dtcm.assign(0x4000,0);
    for (const auto& item:task_aw2::au_manifest().fields) {
        const auto point=item.first.find('.');
        const bool memory=item.first.rfind("code.",0)==0 || item.first.rfind("literal.",0)==0 || item.first.rfind("protected.",0)==0;
        if (!memory && item.first!="dtcm_stack_word") continue;
        const uint32_t address=memory ? std::stoul(item.first.substr(point+1),nullptr,16) : 0x027e3658;
        auto& bytes=address>=0x027e0000 ? g_dtcm : g_main_ram;
        const auto offset=address-(address>=0x027e0000 ? 0x027e0000u : 0x02000000u);
        const auto value=saved.get(item.first);
        for (unsigned index=0;index<item.second.width;++index) bytes.at(offset+index)=uint8_t(value>>(index*8));
    }
    g_last_code_pc[0]=saved.get("hidden.code_pc9"); g_last_code_pc[1]=saved.get("hidden.code_pc7");
    g_last_data_addr[0]=saved.get("hidden.data_addr9"); g_last_data_addr[1]=saved.get("hidden.data_addr7");
    g_arm9_code_timing={uint32_t(saved.get("hidden.cache_page")),uint32_t(saved.get("hidden.cache_generation")),Arm9CodeTiming(saved.get("hidden.cache_class"))};
    g_arm9_region_code_timing=Arm9CodeTiming(saved.get("hidden.region_class"));
    g_arm9_region_code_timing_valid=saved.get("hidden.region_valid");
    arm9_code_fast_publish();
    bind("mainram",brainage_custom::resource_detail::sha256(g_main_ram.data(),g_main_ram.size()));
    bind("dtcm",brainage_custom::resource_detail::sha256(g_dtcm.data(),g_dtcm.size()));
}
uint32_t scalar(uint32_t address,unsigned width) {
    const bool dtcm=address>=0x027e0000 && address<0x027e4000;
    const auto& bytes=dtcm ? g_dtcm : g_main_ram;
    const auto offset=address-(dtcm ? 0x027e0000u : 0x02000000u);
    require(width<=4 && uint64_t(offset)+width<=bytes.size(),"fixture-only direct scalar read, never MMIO");
    uint32_t value=0;
    for (unsigned index=0;index<width;++index) value|=uint32_t(bytes.at(offset+index))<<(index*8);
    return value;
}
uint32_t fetch_cost(uint32_t pc) { return runtime_code_cycles(pc); }
uint32_t data_cost(uint32_t address,unsigned width,bool) { return runtime_mem_cycles(address,width,0); }
uint32_t refill_cost(uint32_t pc) { return arm9_refill_cycles(pc); }
std::vector<uint8_t> ram_copy() { return g_main_ram; }
std::vector<uint8_t> dtcm_copy() { return g_dtcm; }
void bus_mutate(const std::string& name) {
    if (name=="mainram") g_main_ram.at(0x80)^=1;
    else if (name=="dtcm") g_dtcm.at(0x80)^=1;
    else if (name=="code") g_main_ram.at(0x1980)^=1;
    else if (name=="latch") g_last_data_addr[0]^=4;
    else require(false,"unknown bus mutation");
}
}
