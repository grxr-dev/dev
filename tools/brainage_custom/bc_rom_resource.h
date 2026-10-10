#pragma once
#include "bc_resource_hash.h"
#include <stdexcept>
namespace brainage_custom {
class VerifiedBrainAgeRom {
    const uint8_t* bytes_ = nullptr;
    size_t size_ = 0;
public:
    void bind(const char* verified_sha1, const uint8_t* bytes, size_t size) {
        bytes_ = nullptr; size_ = 0;
        if(verified_sha1 && std::string(verified_sha1)=="b8a105bacc3234dede8d4465df0869f2b922a0e2") {bytes_=bytes;size_=size;}
    }
    std::vector<uint8_t> database() const {
        if(!bytes_ || size_<0x796e00+113956)throw std::runtime_error("active verified Brain Age ROM unavailable");
        auto word=[&](size_t a){if(a>size_-4)throw std::runtime_error("ROM bounds");return uint32_t(bytes_[a])|uint32_t(bytes_[a+1])<<8|uint32_t(bytes_[a+2])<<16|uint32_t(bytes_[a+3])<<24;};
        // Task U identified /data/Decuma/_databas_le.bin as FAT file 55.
        const auto fat=word(0x48);const auto fat_size=word(0x4c);
        if(fat_size<56*8 || uint64_t(fat)+fat_size>size_ || word(fat+55*8)!=0x796e00 || word(fat+55*8+4)!=0x796e00+113956)
            throw std::runtime_error("Decuma FAT identity mismatch");
        const auto* data=bytes_+0x796e00;
        if(resource_detail::sha256(data,113956)!="2f237cc7009314df560311a7c026f2fcf6a47b039f6ad7a70443407ef56db0ad")throw std::runtime_error("Decuma resource hash mismatch");
        return {data,data+113956};
    }
};
inline VerifiedBrainAgeRom active_rom;
}
