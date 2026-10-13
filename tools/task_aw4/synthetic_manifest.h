#pragma once
#include "aw3/bridge.h"
namespace task_aw4 {
inline task_aw2::Snapshot synthetic_authority() {
    auto authority=task_aw2::au_manifest();
    std::vector<uint8_t> ram(0x400000),dtcm(0x4000),save(262144,0xa5);
    for (const auto& item:authority.fields) {
        const auto point=item.first.find('.');
        const bool memory=item.first.rfind("code.",0)==0 || item.first.rfind("literal.",0)==0 || item.first.rfind("protected.",0)==0;
        if (!memory && item.first!="dtcm_stack_word") continue;
        const uint32_t address=memory ? std::stoul(item.first.substr(point+1),nullptr,16) : 0x027e3658;
        auto& bytes=address>=0x027e0000 ? dtcm : ram;
        const auto offset=address-(address>=0x027e0000 ? 0x027e0000u : 0x02000000u);
        for (unsigned index=0;index<item.second.width;++index) bytes.at(offset+index)=uint8_t(item.second.value>>(index*8));
    }
    authority.hashes["mainram"]=brainage_custom::resource_detail::sha256(ram.data(),ram.size());
    authority.hashes["dtcm"]=brainage_custom::resource_detail::sha256(dtcm.data(),dtcm.size());
    authority.hashes["save"]=brainage_custom::resource_detail::sha256(save.data(),save.size());
    const std::string identity="AW4 ROM-free fixture identity; not Brain Age";
    authority.hashes["rom"]=gba::sha1(reinterpret_cast<const uint8_t*>(identity.data()),identity.size()).hex();
    return authority;
}
}
