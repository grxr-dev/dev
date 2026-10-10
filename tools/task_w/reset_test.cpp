#include <cstdint>
#include <vector>
#include <cassert>
#include <fstream>
#include <iterator>
#include <cstdio>
static std::vector<uint8_t> live_code;
static uint8_t bus_debug_read8(int cpu,uint32_t a){assert(cpu==9&&a>=0x02000000&&a-0x02000000<live_code.size());return live_code[a-0x02000000];}
#include "bc_private_digit_recognizer.h"
std::vector<uint8_t> read(const char* p){std::ifstream f(p,std::ios::binary);assert(f);return {(std::istreambuf_iterator<char>(f)),{}};}
struct Observed{bool available;uint16_t code;uint32_t metric;uint64_t instructions;bool operator==(const Observed& b)const{return available==b.available&&code==b.code&&metric==b.metric&&instructions==b.instructions;}};
int main(int argc,char**argv){
    assert(argc==4);auto rom=read(argv[1]);live_code=read(argv[2]);const auto before=live_code;std::ifstream fixture(argv[3]);assert(fixture);
    using namespace brainage_custom;active_rom.bind("b8a105bacc3234dede8d4465df0869f2b922a0e2",rom.data(),rom.size());digit_detail::PrivateDigitRecognizer recognizer;
    std::vector<std::vector<Observed>> sequences;
    for(unsigned glyph=0;glyph<3;++glyph){assert(!recognizer.active());auto init=recognizer.begin_session();assert(init.success&&init.instructions==15069&&recognizer.active());unsigned strokes;fixture>>strokes;std::vector<Observed> sequence;
        for(unsigned s=0;s<strokes;++s){unsigned n;fixture>>n;decuma::Stroke points;for(unsigned j=0;j<n;++j){int x,y;fixture>>x>>y;points.push_back({x,y});}assert(fixture);auto v=recognizer.recognize_stroke(points);assert(v.success&&v.error==0);sequence.push_back({v.candidate_available,v.candidate_available?v.candidate:uint16_t(0),v.metric,v.instructions});}
        sequences.push_back(sequence);auto end=recognizer.end_session();assert(end.success&&end.error==0&&end.instructions==13160&&!recognizer.active());assert(live_code==before);
    }
    assert(sequences[0]==sequences[2]);std::puts("PASS: same production object 0 -> teardown -> 1 -> teardown -> 0, identical availability/code/metric/private instructions, inactive after each teardown and unchanged source image");
}
