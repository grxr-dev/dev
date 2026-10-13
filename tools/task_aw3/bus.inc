namespace task_aw3 {
void bus_snapshot(Snapshot& out) {
    require(g_main_ram.size()==0x400000 && g_dtcm.size()==0x4000,"immutable image sizes");
    auto read_scalar=[&](uint32_t address,unsigned width) {
        uint32_t result=0;
        const bool dtcm=address>=0x027e0000 && address<0x027e4000;
        const auto& bytes=dtcm ? g_dtcm : g_main_ram;
        const auto offset=address-(dtcm ? 0x027e0000u : 0x02000000u);
        require(width<=4 && uint64_t(offset)+width<=bytes.size(),"protected direct memory range");
        for (unsigned index=0;index<width;++index) result|=uint32_t(bytes[offset+index])<<(index*8);
        return result;
    };
    for (const auto& item:task_aw2::au_manifest().fields) {
        uint32_t address=0;
        const auto point=item.first.find('.');
        if (item.first.rfind("code.",0)==0 || item.first.rfind("literal.",0)==0 || item.first.rfind("protected.",0)==0)
            address=uint32_t(std::stoul(item.first.substr(point+1),nullptr,16));
        if (address) out.put(item.first,item.second.width,read_scalar(address,item.second.width));
    }
    out.put("dtcm_stack_word",4,read_scalar(0x027e3658,4));
    out.hashes["mainram"]=brainage_custom::resource_detail::sha256(g_main_ram.data(),g_main_ram.size());
    out.hashes["dtcm"]=brainage_custom::resource_detail::sha256(g_dtcm.data(),g_dtcm.size());
    out.put("hidden.code_pc9",4,g_last_code_pc[0]); out.put("hidden.code_pc7",4,g_last_code_pc[1]);
    out.put("hidden.data_addr9",4,g_last_data_addr[0]); out.put("hidden.data_addr7",4,g_last_data_addr[1]);
    out.put("hidden.cache_page",4,g_arm9_code_timing.page);
    out.put("hidden.cache_generation",4,g_arm9_code_timing.cp15_generation);
    out.put("hidden.cache_class",4,uint32_t(g_arm9_code_timing.timing));
    out.put("hidden.region_class",4,uint32_t(g_arm9_region_code_timing));
    out.put("hidden.region_valid",1,g_arm9_region_code_timing_valid);
    out.put("hidden.class_ready",1,g_cp15_class_ready);
    out.put("timing.class",4,g_arm9_code_class_shift/8); out.put("timing.valid",1,g_arm9_code_pub_gen!=0);
    out.put("timing.generation",4,g_arm9_code_pub_gen); out.put("timing.publication",4,g_arm9_code_pub_gen);
    for (const auto address:task_aw2::pcs) {
        const auto page=address>>12;
        out.put(task_aw2::address_key("hidden.code_bit.",address),1,(g_cp15_icache_page[page>>3]>>(page&7))&1);
    }
    for (const uint32_t address:{0x020019acu,0x020019e4u,0x04000280u,0x04000290u,0x04000294u,0x04000298u,0x0400029cu}) {
        const auto page=address>>12;
        out.put(task_aw2::address_key("hidden.data_bit.",address),1,(g_cp15_dcache_page[page>>3]>>(page&7))&1);
    }
}
}
