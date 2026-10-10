#pragma once
#include <array>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>
#include <stdexcept>
#include <cstring>
#include "bus.h"
#include "cpu_state.h"
#include "interpreter.h"
#include "arm_decode.h"
#include "thumb_decode.h"
#include "task_s_adapter.h"
namespace task_u {
inline const char* root(){return std::getenv("NDS_TASK_U_OUT");}
inline void require(bool b,const char* why){if(!b)throw std::runtime_error(why);}
inline void dump(const std::string& name,const std::vector<uint8_t>& b){std::ofstream f(std::string(root())+"/"+name,std::ios::binary);f.write(reinterpret_cast<const char*>(b.data()),b.size());require(bool(f),"dump failed");}
inline std::vector<uint8_t> live(){std::vector<uint8_t>b(0x400000);for(unsigned i=0;i<b.size();++i)b[i]=bus_debug_read8(9,0x02000000+i);return b;}
struct Region {uint32_t address;std::vector<uint8_t> bytes;bool writable;};
struct Session final:armv4t::Bus {
 static constexpr uint32_t ctx=0x02200000,points=0x0220b000,desc=0x0220f000,out=0x0220f100,config=0x0220f200,counts=0x0220f300,stack=0x02210000,db=0x02220000,sp=0x02217fc0,gate=0x02051af8;
 std::vector<Region> regions;
 std::ofstream log;
 uint64_t steps=0,writes=0;
 Session(const std::vector<uint8_t>& ram):log(std::string(root())+"/calls.jsonl") {
  regions.push_back({0x02000000,std::vector<uint8_t>(ram.begin(),ram.begin()+0xd2ba0),false});
  for(auto pair:std::vector<std::pair<uint32_t,unsigned>>{{ctx,0xa350},{points,0x4000},{desc,0x100},{out,0x100},{config,16},{counts,8},{stack,0x8000}})regions.push_back({pair.first,std::vector<uint8_t>(pair.second),true});
  std::ifstream f(std::string(root())+"/database.bin",std::ios::binary);std::vector<uint8_t>b((std::istreambuf_iterator<char>(f)),{});require(b.size()==113956,"database size");regions.push_back({db,std::move(b),false});
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
 void capture(const std::string& tag){for(auto&r:regions)if(r.writable)dump(tag+"-"+std::to_string(r.address)+".bin",r.bytes);}
 // Private fixed sequence; no externally selectable PC or register RPC.
 void invoke(unsigned operation,unsigned stroke=0){
  require(operation<4,"fixed operation only");const uint32_t targets[]={0x020a447c,0x020a41a0,0x020a3fb8,0x020a4440};
  armv4t::CPUState c{};c.cpsr.mode=0x1f;c.cpsr.i=true;c.cpsr.f=true;c.R[0]=ctx;c.R[13]=sp;c.R[14]=gate;c.R[15]=targets[operation];
  if(operation==0){c.R[1]=config;c.R[2]=16;c.R[3]=1;}
  if(operation==1){c.R[1]=desc+stroke*8;c.R[2]=stroke;c.R[3]=out;unsigned j=0;for(uint32_t v:{16u,counts,out+32,16u,counts+4})write32(sp+4*j++,v);write32(counts,0);write32(counts+4,0);}
  if(operation==2){c.R[1]=1;c.R[2]=0;c.R[3]=out+64;}
  auto initial=c;auto start=steps;std::string tag=std::to_string(operation)+"-"+std::to_string(stroke);capture(tag+"-before");
  while(c.R[15]!=gate){
   require(++steps-start<10000000,"instruction bound");auto pc=c.R[15];require(pc>=0x02000000&&pc<0x020d2ba0,"execution outside live title code");
   require(pc!=0x020266b4&&pc!=0x02025778&&pc!=0x02025698&&pc!=0x02027a28&&pc!=0x020531c8,"forbidden scene/worker setup");
   require(c.R[13]>=stack+256&&c.R[13]<=stack+0x8000,"isolated stack bounds");
   auto in=c.cpsr.t?armv4t::ThumbDecoder::decode(read16(pc),pc):armv4t::ArmDecoder::decode(read32(pc),pc);
   auto result=armv4t::Interpreter::step(c,*this,in);
   require(result==armv4t::Interpreter::Result::Normal||result==armv4t::Interpreter::Result::Branched,"exception or unsupported instruction");
  }
  require(c.R[13]==sp,"unbalanced stack");for(unsigned i=4;i<12;++i)require(c.R[i]==initial.R[i],"callee saved mismatch");capture(tag+"-after");
  log<<"{\"operation\":"<<operation<<",\"stroke\":"<<stroke<<",\"target\":"<<targets[operation]<<",\"return\":"<<c.R[0]<<",\"instructions\":"<<steps-start<<",\"candidate\":"<<read16(out+32)<<",\"metric\":"<<read32(out+64)<<",\"count0\":"<<read32(counts)<<",\"count1\":"<<read32(counts+4)<<"}\n";log.flush();
  require(c.R[0]==0,"lifecycle call returned error");
 }
 void run(){invoke(0);require(read32(ctx+0x94dc)==ctx+0x94e0&&read32(ctx+0x94d0)==db&&read32(ctx+0x94bc)==16&&read32(ctx+0x94c0)==1,"initialized context shape");auto enc=task_s::encode(task_s::source(false),points);for(unsigned i=0;i<enc.points.size();++i)write8(points+i,enc.points[i]);for(unsigned i=0;i<enc.descriptors.size();++i)write8(desc+i,enc.descriptors[i]);for(unsigned i=0;i<2;++i){invoke(1,i);require(read16(out+32)==(i?52:50),"known glyph differs; stop");invoke(2,i);}invoke(3);}
};
inline bool done=false;
inline bool stop_rules(uint32_t pc){
 if(root()&&done&&g_nds_active==NDS_ARM9&&pc==0x020610b4){std::ofstream f(std::string(root())+"/continuation.json");f<<"{\"pc\":33951924,\"current\":"<<brainage_custom::peek_word(0x020da464)<<",\"requested\":"<<brainage_custom::peek_word(0x020da3ec)<<",\"selected\":"<<brainage_custom::peek_word(0x020da3f0)<<"}";nds_halt("Task U reached rules entry after teardown");return true;}return false;
}
inline void hook(){
 if(stop_rules(g_cpu.R[15]))return;
 if(!done&&g_nds_active==NDS_ARM9&&g_cpu.R[15]==0x0204d790&&g_cpu.R[0]==0x41){
  done=true;const auto cpu=g_cpu;auto before=live();auto cyc=g_runtime_cycles;auto c7=scheduler_cpu_cycles(1);auto i9=g_insn_count[0],i7=g_insn_count[1];dump("before-mainram.bin",before);
  try {require(!g_nds_force_tier3,"compiled boundary required");require(brainage_custom::peek_word(0x020da464)==0x32&&brainage_custom::peek_word(0x020da3ec)==0x41&&brainage_custom::peek_word(0x020da3f0)==0x11,"boundary scene mismatch");
   {Session s(before);s.run();} // owned resource/code/context/scratch backing is destroyed here
   auto after=live();dump("after-mainram.bin",after);require(before==after,"live RAM changed");require(std::memcmp(&cpu,&g_cpu,sizeof(cpu))==0,"live CPU changed");require(cyc==g_runtime_cycles&&c7==scheduler_cpu_cycles(1)&&i9==g_insn_count[0]&&i7==g_insn_count[1],"live guest counters advanced");
   std::ofstream f(std::string(root())+"/success.json");f<<"{\"policy\":\"A\",\"cycles9_before_after\":"<<cyc<<",\"cycles7_before_after\":"<<c7<<",\"instructions9_before_after\":"<<i9<<",\"instructions7_before_after\":"<<i7<<",\"live_ram_equal\":true,\"live_cpu_equal\":true,\"owned_session_destroyed\":true}";
  }catch(const std::exception&e){std::ofstream f(std::string(root())+"/error.txt");f<<e.what();nds_halt("Task U isolated diagnostic failed");return;}
 }
 brainage_custom::compiled_instruction();
}
inline void install(){if(root()&&*root()){require(!brainage_custom::enabled,"production host must be off");nds_set_compiled_instruction_hook(hook);}}
}
