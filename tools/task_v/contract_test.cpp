#include <cassert>
#include <fstream>
#include <iterator>
#include <cstdio>
#include "bc_catalog.h"
#include "bc_resource_hash.h"
#include "../task_s/adapter.h"
using namespace brainage_custom;
struct Fake final:DigitRecognizer {
    bool live=false, fail_init=false, fail_call=false;
    unsigned calls=0;
    DigitResult begin_session()override{live=!fail_init;return {live,false,0,0,0,0,0,{}};}
    DigitResult recognize_stroke(const decuma::Stroke&)override{++calls;return {!fail_call,!fail_call, uint16_t('7'),0,fail_call?1u:0u,0,0,{}};}
    DigitResult end_session()override{live=false;return {true,false,0,0,0,0,0,{}};}
    bool active()const override{return live;}
};
int main(){
    auto known=task_s::source(false);decuma::Strokes converted;
    for(auto& s:known){converted.emplace_back();for(auto v:s)converted.back().push_back({v.x,v.y});}
    auto old=task_s::encode(known,0x0220b000);auto now=decuma::encode(converted,0x0220b000);
    assert(old.points==now.points&&old.descriptors==now.descriptors);
    for(auto input:{decuma::Strokes{},decuma::Strokes{{}},decuma::Strokes{{{-1,0}}},decuma::Strokes{{{256,0}}},decuma::Strokes{{{0,192}}},decuma::Strokes(33,{{1,1}}),decuma::Strokes{decuma::Stroke(4097,{1,1})}}){bool rejected=false;try{decuma::encode(input,0x0220b000);}catch(...){rejected=true;}assert(rejected);}
    bool rejected=false;try{decuma::encode({{{1,1}}},0xfffffff0);}catch(...){rejected=true;}assert(rejected);
    auto text=std::string("abc");assert(resource_detail::sha256(reinterpret_cast<const uint8_t*>(text.data()),text.size())=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    assert(std::string(exercise_descriptor("digit-recognition-probe").id)=="digit-recognition-probe");
    for(unsigned mode=0;mode<3;++mode){Fake f;f.fail_init=mode==1;f.fail_call=mode==2;ExerciseServices services{&f};auto e=exercise_descriptor("digit-recognition-probe").create(services);e->begin();
        if(!f.fail_init){for(unsigned s=0;s<2;++s){if(f.fail_call&&s)break;assert(!e->status().can_continue);for(auto v:converted[s])e->touch(v.x,v.y,true);e->touch(converted[s].back().x,converted[s].back().y,true);e->touch(0,0,false);} }
        assert(e->status().can_continue);const auto count=f.calls;e->touch(100,100,true);e->touch(0,0,false);assert(f.calls==count);
        e->touch(128,166,true);assert(!e->status().can_continue);assert(e->touch(0,0,false).request_exit);e.reset();f.end_session();assert(!f.active());
    }
    auto missing=exercise_descriptor("digit-recognition-probe").create();missing->begin();assert(missing->status().can_continue);
    std::puts("PASS: adapter parity/bounds/SHA256, selector, candidate-independent exit, error exit and no third stroke");
}
