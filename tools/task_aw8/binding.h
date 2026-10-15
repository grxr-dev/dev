#pragma once
#if !defined(AW8_ROMFREE_FIXTURE)
#error AW8 historical observation binding is test-executable-only
#endif
#include <fstream>
#include "aw7/integration.h"

namespace task_aw8 {
using task_aw2::require;
inline std::shared_ptr<const task_aw2::Snapshot> evidence;
struct BoundIdentity { std::string local, historical; };
inline std::map<std::string,BoundIdentity> bindings;
inline std::shared_ptr<const std::map<std::string,BoundIdentity>> sealed_bindings;
inline bool sealed=false;
inline unsigned identity_reads=0,mutate_at_read=0;
inline void (*sample_mutation)()=nullptr;
inline const task_aw2::Snapshot& entry() { require(bool(evidence),"authenticated AW5 evidence missing"); return *evidence; }
inline void load(const char* path) {
    require(!evidence && !sealed,"evidence already loaded");
    std::ifstream input(path); std::string hex; input>>hex;
    require(input.good() || input.eof(),"canonical evidence input");
    require(!hex.empty() && hex.size()<1048576 && hex.size()%2==0 &&
        hex.find_first_not_of("0123456789abcdef")==std::string::npos,"canonical evidence encoding");
    std::string extra;
    require(!(input>>extra),"trailing canonical evidence data");
    std::vector<uint8_t> bytes;
    for (size_t index=0;index<hex.size();index+=2) bytes.push_back(uint8_t(std::stoul(hex.substr(index,2),nullptr,16)));
    const auto observed=task_aw2::decode(bytes);
    require(task_aw2::canonical(observed)==bytes && task_aw2::digest(observed)==task_aw6::entry_identity,
        "AW5 canonical authentication");
    require(observed.fields.size()==361 && observed.hashes.size()==5,"AW5 complete observation set");
    evidence=std::make_shared<const task_aw2::Snapshot>(observed);
}
inline void bind(const std::string& name,const std::string& computed) {
    require(!sealed && !bindings.count(name) && entry().hashes.count(name),"identity binding lifecycle");
    require(!computed.empty(),"missing computed local identity");
    bindings.emplace(name,BoundIdentity{computed,entry().hashes.at(name)});
}
inline std::string identity(const std::string& name,const std::string& computed) {
    require(sealed && sealed_bindings && sealed_bindings->count(name),"unsealed identity observation");
    require(task_aw2::digest(entry())==task_aw6::entry_identity,"authenticated immutable evidence changed");
    const auto& bound=sealed_bindings->at(name);
    require(bound.local==computed && bound.historical==entry().hashes.at(name),"immutable identity observation changed: "+name);
    if (++identity_reads==mutate_at_read && sample_mutation) sample_mutation();
    return bound.historical;
}
inline void seal() {
    require(!sealed && bindings.size()==4 && bindings.count("mainram") && bindings.count("dtcm") &&
        bindings.count("save") && bindings.count("rom"),"complete immutable evidence binding");
    sealed_bindings=std::make_shared<const std::map<std::string,BoundIdentity>>(bindings);
    sealed=true;
}
inline void audit_binding() {
    for (const auto& item:*sealed_bindings)
        std::fprintf(task_aw3::output,"{\"event\":\"historical_identity_binding\",\"identity\":\"%s\",\"local_surrogate_digest\":\"%s\",\"authenticated_AW5_digest\":\"%s\",\"new_measurement_of_AW5_image\":false}\n",
            item.first.c_str(),item.second.local.c_str(),item.second.historical.c_str());
}
void runtime_begin();
void bus_begin();
void cp15_begin();
void io_begin();
void scheduler_begin();
void spu_begin();
void fetch();
void commit(unsigned,uint32_t);
void retire(unsigned);
uint32_t fetch_cost(uint32_t);
uint32_t data_cost(uint32_t,unsigned,bool);
uint32_t refill_cost(uint32_t);
uint32_t scalar(uint32_t,unsigned);
void model_write(unsigned);
std::vector<uint8_t> ram_copy();
std::vector<uint8_t> dtcm_copy();
std::vector<uint8_t> save_copy();
void runtime_mutate(const std::string&);
void bus_mutate(const std::string&);
void io_mutate(const std::string&);
void scheduler_mutate(const std::string&);
}
