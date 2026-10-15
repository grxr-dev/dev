#include <fstream>
#include <iostream>
#include "aw4/reconcile.h"

template<class Check> void report(const char* name,Check check) {
    try { check(); std::cout<<name<<": PASS\n"; }
    catch (const std::exception& error) { std::cout<<name<<": REJECT "<<error.what()<<"\n"; }
}
int main(int argc,char** argv) {
    try {
        task_aw2::require(argc==2,"canonical hex file required");
        std::ifstream input(argv[1]);
        std::string text;
        input>>text;
        task_aw2::require(input.good() || input.eof(),"hex input read");
        task_aw2::require(text.size()%2==0,"hex input width");
        std::vector<uint8_t> bytes;
        for (size_t index=0;index<text.size();index+=2)
            bytes.push_back(uint8_t(std::stoul(text.substr(index,2),nullptr,16)));
        const auto observed=task_aw2::decode(bytes);
        task_aw2::require(task_aw2::canonical(observed)==bytes,"round-trip canonical bytes");
        std::cout<<"canonical_sha256: "<<task_aw2::digest(observed)<<"\n";
        report("full_schema",[&] { task_aw4::full_schema(observed); });
        report("AU_manifest",[&] { task_aw2::manifest_matches(observed); });
        report("journal",[&] { task_aw4::journal_valid(observed); });
        report("AW2_core_preflight",[&] { task_aw2::preflight(task_aw3::core_projection(observed)); });
        report("first_prospective_guard",[&] { task_aw2::prospective(observed,0); });
        report("AW4_first_write_shortens",[&] {
            task_aw2::require(observed.get("slice_cap")>task_aw2::twice(task_aw2::add(observed.get("cycle9")>>1,34)),
                "existing cap is earlier than first divider deadline");
        });
        report("RTC_phase",[&] {
            task_aw2::require(observed.get("service.rtc_processed")==observed.get("service.rtc_due"),"processed differs from floor-derived due");
        });
        uint64_t total=0;
        for (unsigned index=0;index<task_aw2::pcs.size();++index) {
            const auto cost=task_aw2::cost(observed,index);
            total=task_aw2::add(total,cost);
            std::cout<<"cost["<<index<<"]="<<cost<<"\n";
        }
        std::cout<<"modeled_cost_sum: "<<total<<"\n";
        return 0;
    } catch (const std::exception& error) { std::cerr<<error.what()<<"\n"; return 1; }
}
