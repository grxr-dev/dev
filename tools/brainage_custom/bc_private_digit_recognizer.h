#pragma once
#include <array>
#include <chrono>
#include <memory>
#include <stdexcept>
#include "bus.h"
#include "cpu_state.h"
#include "interpreter.h"
#include "arm_decode.h"
#include "thumb_decode.h"
#include "bc_digit_recognizer.h"
#include "bc_rom_resource.h"
namespace brainage_custom::digit_detail {
inline void require(bool b,const char* why){if(!b)throw std::runtime_error(why);}
class PrivateDigitRecognizer;
class PrivateDecumaSession final:public armv4t::Bus {
public:
 ~PrivateDecumaSession() override = default;
private:
 friend class PrivateDigitRecognizer;
 static constexpr uint32_t ctx=0x02200000,points=0x0220b000,desc=0x0220f000,out=0x0220f100,config=0x0220f200,counts=0x0220f300,stack=0x02210000,db=0x02220000,sp=0x02217fc0,gate=0x02051af8;
 struct Region {uint32_t address;std::vector<uint8_t> bytes;bool writable;};
 std::vector<Region> regions;

 uint64_t steps=0,writes=0;
 PrivateDecumaSession(std::vector<uint8_t> code,std::vector<uint8_t> database) {
  require(code.size()==0xd2ba0,"code snapshot size");require(database.size()==113956,"database size");
  regions.push_back({0x02000000,std::move(code),false});
  for(auto pair:std::vector<std::pair<uint32_t,unsigned>>{{ctx,0xa350},{points,0x4000},{desc,0x100},{out,0x100},{config,16},{counts,8},{stack,0x8000}})regions.push_back({pair.first,std::vector<uint8_t>(pair.second),true});
  regions.push_back({db,std::move(database),false});
  write32(config,db);write16(config+12,159);write16(config+14,111);
 }
 uint8_t read8(uint32_t a) override {for(auto&r:regions)if(a>=r.address&&a-r.address<r.bytes.size())return r.bytes[a-r.address];throw std::runtime_error("unmapped isolated read "+std::to_string(a));}
 uint16_t read16(uint32_t a) override{return read8(a)|(uint16_t(read8(a+1))<<8);}
 uint32_t read32(uint32_t a) override{return read16(a)|(uint32_t(read16(a+2))<<16);}
 void write8(uint32_t a,uint8_t v) override{for(auto&r:regions)if(a>=r.address&&a-r.address<r.bytes.size()){require(r.writable,"write to code/database");r.bytes[a-r.address]=v;++writes;return;}throw std::runtime_error("unmapped isolated write "+std::to_string(a));}
 void write16(uint32_t a,uint16_t v) override{write8(a,uint8_t(v));write8(a+1,uint8_t(v>>8));}
 void write32(uint32_t a,uint32_t v) override{write16(a,uint16_t(v));write16(a+2,uint16_t(v>>16));}
 void coproc_write(uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t)override{throw std::runtime_error("coprocessor write forbidden");}
 uint32_t coproc_read(uint32_t,uint32_t,uint32_t,uint32_t,uint32_t)override{throw std::runtime_error("coprocessor read forbidden");}
 void coproc_cdp(uint32_t,uint32_t,uint32_t,uint32_t,uint32_t)override{throw std::runtime_error("coprocessor operation forbidden");}
 // Private fixed sequence; no externally selectable PC or register RPC.
 uint32_t invoke(unsigned operation,unsigned stroke=0,unsigned group=1,unsigned index=0){
  require(operation<5&&group<2&&index<15,"fixed operation and bounded character only");const uint32_t targets[]={0x020a447c,0x020a41a0,0x020a3fb8,0x020a4440,0x020a3ffc};
  armv4t::CPUState c{};c.cpsr.mode=0x1f;c.cpsr.i=true;c.cpsr.f=true;c.R[0]=ctx;c.R[13]=sp;c.R[14]=gate;c.R[15]=targets[operation];
  if(operation==0){c.R[1]=config;c.R[2]=16;c.R[3]=1;}
  if(operation==1){c.R[1]=desc+stroke*8;c.R[2]=stroke;c.R[3]=out;unsigned j=0;for(uint32_t v:{16u,counts,out+32,16u,counts+4})write32(sp+4*j++,v);write32(counts,0);write32(counts+4,0);}
  if(operation==2){c.R[1]=1;c.R[2]=0;c.R[3]=out+64;}
  if(operation==4){c.R[1]=group;c.R[2]=index;c.R[3]=out+96;write32(sp,16-index);write32(sp+4,0);write32(sp+8,0);for(unsigned j=0;j<32;++j)write8(out+96+j,0);}
  auto initial=c;auto start=steps;
  while(c.R[15]!=gate){
   require(++steps-start<10000000,"instruction bound");auto pc=c.R[15];require(pc>=0x02000000&&pc<0x020d2ba0,"execution outside live title code");
   require(pc!=0x020266b4&&pc!=0x02025778&&pc!=0x02025698&&pc!=0x02027a28&&pc!=0x020531c8&&pc!=0x02051a30&&pc!=0x0205330c&&pc!=0x02005710&&pc!=0x020508f0&&pc!=0x0205092c,"forbidden scene/worker setup");
   require(c.R[13]>=stack+256&&c.R[13]<=stack+0x8000,"isolated stack bounds");
   auto in=c.cpsr.t?armv4t::ThumbDecoder::decode(read16(pc),pc):armv4t::ArmDecoder::decode(read32(pc),pc);
   auto result=armv4t::Interpreter::step(c,*this,in);
   require(result==armv4t::Interpreter::Result::Normal||result==armv4t::Interpreter::Result::Branched,"exception or unsupported instruction");
  }
  require(c.R[13]==sp,"unbalanced stack");for(unsigned i=4;i<12;++i)require(c.R[i]==initial.R[i],"callee saved mismatch");
  return c.R[0];
 }
};

class PrivateDigitRecognizer final : public DigitRecognizer {
    std::unique_ptr<PrivateDecumaSession> session;
    unsigned stroke_index=0, point_count=0;
    bool initialized=false;
    using Clock=std::chrono::steady_clock;
    static uint64_t elapsed(Clock::time_point start){return std::chrono::duration_cast<std::chrono::microseconds>(Clock::now()-start).count();}
public:
    ~PrivateDigitRecognizer() override { if(session) { try { end_session(); } catch(...) { std::terminate(); } } }
    bool active() const override {return bool(session);}
    DigitResult begin_session() override {
        if(session)return {false,false,0,0,1,0,0,"session already active"};
        const auto start=Clock::now();
        try {
            auto database=active_rom.database();
            std::vector<uint8_t> code(0xd2ba0);
            for(unsigned i=0;i<code.size();++i)code[i]=bus_debug_read8(9,0x02000000+i);
            session=std::unique_ptr<PrivateDecumaSession>(new PrivateDecumaSession(std::move(code),std::move(database)));
        } catch(const std::runtime_error& e) {session.reset();return {false,false,0,0,1,elapsed(start),0,e.what()};}
        // Private bus/interpreter invariant failures propagate and fail closed.
        auto& s=*session;const auto result=s.invoke(0);initialized=result==0;
        stroke_index=point_count=0;
        if(!initialized){auto count=s.steps;session.reset();return {false,false,0,0,result,elapsed(start),count,"initialization returned error"};}
        require(s.read32(s.ctx+0x94dc)==s.ctx+0x94e0&&s.read32(s.ctx+0x94d0)==s.db&&s.read32(s.ctx+0x94bc)==16&&s.read32(s.ctx+0x94c0)==1,"initialized context shape");
        return {true,false,0,0,0,elapsed(start),s.steps,{}};
    }
    DigitResult recognize_stroke(const decuma::Stroke& stroke) override {
        if(!initialized||!session)return {false,false,0,0,1,0,0,"no session"};
        if(stroke_index>=32 || stroke.empty() || stroke.size()>4096-point_count)return {false,false,0,0,1,0,0,"stroke/point capacity"};
        decuma::Encoded encoded;
        try {encoded=decuma::encode({stroke},PrivateDecumaSession::points+point_count*4);}catch(const std::runtime_error& e){return {false,false,0,0,1,0,0,e.what()};}
        auto& s=*session; const auto start=Clock::now();const auto before=s.steps;
        for(unsigned i=0;i<encoded.points.size();++i)s.write8(s.points+point_count*4+i,encoded.points[i]);
        for(unsigned i=0;i<encoded.descriptors.size();++i)s.write8(s.desc+stroke_index*8+i,encoded.descriptors[i]);
        const auto result=s.invoke(1,stroke_index);++stroke_index;point_count+=unsigned(stroke.size());
        if(result)return {false,false,0,0,result,elapsed(start),s.steps-before,"recognition returned error"};
        const bool available=s.read32(s.counts+4)>0;
        const auto candidate=available?s.read16(s.out+32):uint16_t(0);
        const auto metric_result=s.invoke(2);
        if(metric_result)return {false,false,0,0,metric_result,elapsed(start),s.steps-before,"metric returned error"};
        DigitResult value{true,available,candidate,s.read32(s.out+64),0,0,0,{}};
        for(unsigned g=0;g<2;++g){
            auto& output=value.groups[g];output.returned_count=s.read32(s.counts+4*g);
            require(output.returned_count<=16,"output segment count bound");
            for(unsigned i=0;i<16;++i)output.codes[i]=s.read16(s.out+32*g+2*i);
            while(output.code_count<16&&output.codes[output.code_count])++output.code_count;
            require(output.code_count<16,"unterminated output group");
            for(unsigned i=0;i<output.code_count;++i){
                const auto accessor_result=s.invoke(4,0,g,i);
                if(accessor_result)return {false,false,0,0,accessor_result,elapsed(start),s.steps-before,"character accessor returned error"};
                output.accessor_codes[i]=s.read16(s.out+96);
            }
        }
        value.wall_us=elapsed(start);value.instructions=s.steps-before;return value;
    }
    DigitResult end_session() override {
        const auto start=Clock::now();uint32_t result=0;uint64_t count=0;
        if(session&&initialized){auto& s=*session;auto before=s.steps;result=s.invoke(3);count=s.steps-before;
            require(result==0,"context teardown returned error");for(unsigned i=0;i<0x94e0;++i)require(s.read8(s.ctx+i)==0,"context prefix not cleared");}
        session.reset();initialized=false;stroke_index=point_count=0;
        return {true,false,0,0,result,elapsed(start),count,{}};
    }
};
}
