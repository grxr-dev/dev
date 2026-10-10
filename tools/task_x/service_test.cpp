#include <cstdint>
#include <vector>
#include <cassert>
#include <fstream>
#include <iterator>
#include <cstdio>
static std::vector<uint8_t> live_code;
static uint8_t bus_debug_read8(int cpu,uint32_t address){assert(cpu==9&&address>=0x02000000&&address-0x02000000<live_code.size());return live_code[address-0x02000000];}
#include "bc_private_digit_recognizer.h"
#include "../task_s/adapter.h"
std::vector<uint8_t> read(const char* path){std::ifstream f(path,std::ios::binary);assert(f);return {(std::istreambuf_iterator<char>(f)),{}};}
int main(int argc,char**argv){
    assert(argc==3);auto rom=read(argv[1]);live_code=read(argv[2]);const auto before=live_code;
    using namespace brainage_custom;active_rom.bind("b8a105bacc3234dede8d4465df0869f2b922a0e2",rom.data(),rom.size());
    digit_detail::PrivateDigitRecognizer recognizer;
    assert(!recognizer.active()&&!recognizer.recognize_stroke({{1,1}}).success);
    for(unsigned session=0;session<2;++session){auto init=recognizer.begin_session();assert(init.success&&recognizer.active()&&init.instructions==15069);assert(!recognizer.begin_session().success);
        assert(!recognizer.recognize_stroke({}).success);assert(!recognizer.recognize_stroke({{-1,2}}).success);assert(!recognizer.recognize_stroke(decuma::Stroke(4097,{1,1})).success);
        auto known=task_s::source(false);for(unsigned i=0;i<2;++i){decuma::Stroke stroke;for(auto p:known[i])stroke.push_back({p.x,p.y});auto result=recognizer.recognize_stroke(stroke);assert(result.success&&result.error==0&&result.candidate_available&&result.candidate==(i?'4':'2'));assert(result.metric==(i?249:500));
        assert(result.groups[0].returned_count==0&&result.groups[0].code_count==0);
        assert(result.groups[1].returned_count==1&&result.groups[1].code_count==1);
        assert(result.groups[1].codes[0]==result.candidate&&result.groups[1].codes[1]==0);
        assert(result.groups[1].accessor_codes[0]=='0');
        assert(result.instructions>(i?1561225u:636745u));}
        auto end=recognizer.end_session();assert(end.success&&end.error==0&&end.instructions==13160&&!recognizer.active());assert(recognizer.end_session().success);assert(live_code==before);
    }
    rom[0x796e00]^=1;assert(!recognizer.begin_session().success&&!recognizer.active());rom[0x796e00]^=1;
    active_rom.bind("wrong",rom.data(),rom.size());assert(!recognizer.begin_session().success&&!recognizer.active());
    std::puts("PASS: production service 2 -> 4 twice, session reset, invalid input, fixed original teardown and untouched source snapshot");
}
