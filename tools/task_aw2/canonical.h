#pragma once
#include <cstdint>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
#include "../brainage_custom/bc_resource_hash.h"

namespace task_aw2 {
inline void require(bool condition, const std::string& reason) {
    if (!condition) throw std::runtime_error(reason);
}
inline uint64_t add(uint64_t left, uint64_t right) {
    require(right <= UINT64_MAX-left, "cycle/add overflow");
    return left+right;
}
inline uint64_t twice(uint64_t value) {
    require(value <= UINT64_MAX/2, "half-rate shift overflow");
    return value*2;
}
struct Cell {
    uint8_t width=0;
    uint64_t value=0;
    bool operator==(const Cell& other) const {
        return width==other.width && value==other.value;
    }
};
struct Snapshot {
    std::map<std::string,Cell> fields;
    std::map<std::string,std::string> hashes;
    void put(const std::string& key, uint8_t width, uint64_t value) {
        require(width==1 || width==2 || width==4 || width==8, "field width");
        require(width==8 || value < (uint64_t{1}<<(width*8)), "field overflow");
        fields[key]={width,value};
    }
    uint64_t get(const std::string& key) const {
        const auto found=fields.find(key);
        require(found!=fields.end(), "missing field: "+key);
        return found->second.value;
    }
    bool operator==(const Snapshot& other) const {
        return fields==other.fields && hashes==other.hashes;
    }
};
inline bool identifier(const std::string& text) {
    if (text.empty() || text.size()>128) return false;
    for (unsigned char character:text)
        if (!((character>='a' && character<='z') || (character>='0' && character<='9') ||
              character=='.' || character=='_')) return false;
    return true;
}
inline bool hex_digest(const std::string& text) {
    if (text.size()!=40 && text.size()!=64) return false;
    for (unsigned char character:text)
        if (!((character>='0' && character<='9') || (character>='a' && character<='f'))) return false;
    return true;
}
inline void little(std::vector<uint8_t>& bytes, uint64_t value, unsigned width) {
    for (unsigned index=0;index<width;++index) bytes.push_back(uint8_t(value>>(index*8)));
}
inline void string_bytes(std::vector<uint8_t>& bytes, const std::string& text) {
    require(text.size()<=UINT16_MAX, "string length");
    little(bytes,text.size(),2);
    bytes.insert(bytes.end(),text.begin(),text.end());
}
inline std::vector<uint8_t> canonical(const Snapshot& snapshot) {
    std::vector<uint8_t> bytes={'A','W','2','S',1,0};
    require(snapshot.fields.size()<=4096 && snapshot.hashes.size()<=128, "snapshot size");
    little(bytes,snapshot.fields.size(),4);
    for (const auto& item:snapshot.fields) {
        require(identifier(item.first), "field identifier");
        const auto width=item.second.width;
        require(width==1 || width==2 || width==4 || width==8, "canonical width");
        require(width==8 || item.second.value < (uint64_t{1}<<(width*8)), "canonical overflow");
        string_bytes(bytes,item.first);
        little(bytes,width,1);
        little(bytes,item.second.value,width);
    }
    little(bytes,snapshot.hashes.size(),4);
    for (const auto& item:snapshot.hashes) {
        require(identifier(item.first) && hex_digest(item.second), "digest encoding");
        string_bytes(bytes,item.first);
        string_bytes(bytes,item.second);
    }
    return bytes;
}
struct Reader {
    const std::vector<uint8_t>& bytes;
    size_t cursor=0;
    uint64_t integer(unsigned width) {
        require(width<=8 && cursor<=bytes.size() && width<=bytes.size()-cursor, "truncated canonical bytes");
        uint64_t value=0;
        for (unsigned index=0;index<width;++index) value|=uint64_t(bytes[cursor++])<<(8*index);
        return value;
    }
    std::string text() {
        const auto size=integer(2);
        require(size<=bytes.size()-cursor, "truncated canonical string");
        std::string result(bytes.begin()+cursor,bytes.begin()+cursor+size);
        cursor+=size;
        return result;
    }
};
inline Snapshot decode(const std::vector<uint8_t>& bytes) {
    Reader reader{bytes};
    require(reader.integer(4)==0x53325741 && reader.integer(2)==1, "schema/version");
    Snapshot snapshot;
    auto count=reader.integer(4);
    require(count<=4096, "field count");
    std::string previous;
    for (uint64_t index=0;index<count;++index) {
        auto key=reader.text();
        require(identifier(key) && key>previous, "canonical field ordering/duplicate");
        auto width=reader.integer(1);
        require(width==1 || width==2 || width==4 || width==8, "decoded width");
        snapshot.put(key,uint8_t(width),reader.integer(unsigned(width)));
        previous=key;
    }
    count=reader.integer(4);
    require(count<=128, "hash count");
    previous.clear();
    for (uint64_t index=0;index<count;++index) {
        auto key=reader.text(), hash=reader.text();
        require(identifier(key) && key>previous && hex_digest(hash), "canonical hash ordering/encoding");
        snapshot.hashes[key]=hash;
        previous=key;
    }
    require(reader.cursor==bytes.size(), "extra canonical bytes");
    require(canonical(snapshot)==bytes, "noncanonical representation");
    return snapshot;
}
inline std::string digest(const Snapshot& snapshot) {
    const auto bytes=canonical(snapshot);
    return brainage_custom::resource_detail::sha256(bytes.data(),bytes.size());
}
inline void exact(const Snapshot& actual, const Snapshot& expected) {
    require(actual==expected, "logical snapshot mismatch");
    require(canonical(actual)==canonical(expected), "canonical snapshot mismatch");
}
}
