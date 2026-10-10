#include <cassert>
#include <cstdio>
#include <fstream>
#include "bc_catalog.h"
using namespace brainage_custom;
uint64_t metric(const ExerciseStatus& s,const char* name){for(auto m:s.diagnostics)if(m.name==name)return m.value;assert(false);return 0;}
struct Fake final:DigitRecognizer {
    bool live=false,fail_init=false,fail_call=false;
    unsigned calls=0,points=0;
    DigitResult begin_session()override{live=!fail_init;calls=points=0;return {live,false,0,0,live?0u:8u,0,0,{}};}
    DigitResult recognize_stroke(const decuma::Stroke& s)override{
        assert(live);++calls;points+=unsigned(s.size());
        const bool available=calls==2||calls==3;
        return {!fail_call,available,uint16_t(calls==2?'2':'9'),123,fail_call?7u:0u,0,0,{}};
    }
    DigitResult end_session()override{live=false;return {true,false,0,0,0,0,0,{}};}
    bool active()const override{return live;}
};
void stroke(Exercise& e,unsigned n=3){for(unsigned j=0;j<n;++j){e.touch(j%2?100:101,90,true);assert(!e.status().can_continue);}e.touch(0,0,false);}
void check_text(const Surface& actual,const std::string& text){Surface expected;expected.pixels.fill(0xff172335u);expected.text(74,23,text,0xffedf4ffu);for(unsigned y=23;y<30;++y)for(unsigned x=0;x<256;++x)assert(actual.pixels[y*256+x]==expected.pixels[y*256+x]);}
void ppm(const Surface& s,const char* path){std::ofstream f(path,std::ios::binary);f<<"P6\n256 192\n255\n";for(auto v:s.pixels){f.put(char(v>>16));f.put(char(v>>8));f.put(char(v));}assert(f);}
int main(int argc,char**argv){
    assert(argc==2);Fake f;ExerciseServices services{&f};auto e=exercise_descriptor("digit-entry-probe").create(services);e->begin();assert(f.active());assert(!e->status().can_continue);
    e->touch(100,90,true);e->touch(100,90,true);assert(f.calls==0);e->touch(101,90,true);assert(f.calls==0);e->touch(0,0,false);
    assert(f.calls==1&&f.points==2&&e->status().phase=="no_candidate");assert(metric(e->status(),"recognition_success")&& !metric(e->status(),"recognition_error")&&!metric(e->status(),"candidate_available")&&metric(e->status(),"candidate")==0);
    assert(e->status().can_continue&&!e->status().contact_down);Surface surface;e->render(surface);check_text(surface,"NO CANDIDATE YET");ppm(surface,argv[1]);
    stroke(*e);assert(f.calls==2&&e->status().phase=="candidate"&&metric(e->status(),"candidate")=='2');e->render(surface);check_text(surface,"CANDIDATE: 2");
    stroke(*e);assert(f.calls==3&&metric(e->status(),"candidate")=='9');e->render(surface);check_text(surface,"CANDIDATE: 9");
    e.reset();f.end_session();assert(!f.active());e=exercise_descriptor("digit-entry-probe").create(services);e->begin();stroke(*e);assert(e->status().phase=="no_candidate");e->touch(128,166,true);assert(!e->status().can_continue);assert(e->touch(0,0,false).request_exit);e.reset();f.end_session();assert(!f.active());
    e=exercise_descriptor("digit-entry-probe").create(services);e->begin();for(unsigned i=0;i<8;++i)stroke(*e,64);assert(f.calls==8&&f.points==512&&metric(e->status(),"completed_strokes")==8&&metric(e->status(),"point_count")==512&&!metric(e->status(),"recognition_error"));stroke(*e);assert(f.calls==8);assert(e->status().can_continue);e.reset();f.end_session();
    for(unsigned error=0;error<2;++error){f.fail_init=error==0;f.fail_call=error==1;e=exercise_descriptor("digit-entry-probe").create(services);e->begin();if(!f.fail_init)stroke(*e);assert(e->status().phase=="error"&&e->status().can_continue);e->touch(128,166,true);assert(e->touch(0,0,false).request_exit);e.reset();f.end_session();}
    assert(std::string(exercise_descriptor(nullptr).id)=="arithmetic-2plus2");assert(std::string(exercise_descriptor("freehand-canvas").id)=="freehand-canvas");assert(std::string(exercise_descriptor("digit-recognition-probe").id)=="digit-recognition-probe");bool rejected=false;try{exercise_descriptor("unknown");}catch(...){rejected=true;}assert(rejected);
    std::puts("PASS: successful no-candidate phase/render/continued capture/safe exit, later candidate replacement, 8 strokes/512 points, error exit, selectors");
}
