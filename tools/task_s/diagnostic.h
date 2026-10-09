#pragma once
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>
#include <optional>
#include <algorithm>
#include "state.h"
#include "task_s_adapter.h"
namespace task_s {
inline bool active=false,done=false;inline unsigned stroke=0,phase=0,write_seq=0;
inline uint32_t exercise=0,manager=0,slot=0,context=0,points=0,descriptors=0,arena=0,counts=0,call_sp=0,min_sp=0;
inline uint64_t start_cycles=0;inline std::vector<uint8_t> exercise_before,guard;
inline const char* root(){static const char* p=std::getenv("NDS_TASK_S_OUT");return p;}
inline uint32_t word(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v|=uint32_t(bus_debug_read8(9,a+i))<<(i*8);return v;}
inline std::vector<uint8_t> read(uint32_t a,unsigned n){std::vector<uint8_t>b(n);for(unsigned i=0;i<n;++i)b[i]=bus_debug_read8(9,a+i);return b;}
inline void file(const std::string& name,const std::vector<uint8_t>& b){FILE*f=std::fopen((std::string(root())+"/"+name).c_str(),"wb");if(!f)throw std::runtime_error("diagnostic file open failed");std::fwrite(b.data(),1,b.size(),f);std::fclose(f);}
inline void json(const std::string& s){FILE*f=std::fopen((std::string(root())+"/calls.jsonl").c_str(),"ab");if(!f)throw std::runtime_error("diagnostic log failed");std::fprintf(f,"%s\n",s.c_str());std::fclose(f);}
inline void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
inline bool ram(uint32_t p,unsigned n){return p>=0x020d3218u && p<0x02400000u && n<=0x02400000u-p;}
inline void write(uint32_t a,const std::vector<uint8_t>& b,const char* purpose){
 bool allowed=(a>=points&&uint64_t(a)+b.size()<=uint64_t(points)+0x4000)||(a>=descriptors&&uint64_t(a)+b.size()<=uint64_t(descriptors)+0x100)||(a>=arena&&uint64_t(a)+b.size()<=uint64_t(arena)+0x4000)||(a>=counts&&uint64_t(a)+b.size()<=uint64_t(counts)+0x100);
 check(allowed,"adapter write outside verified allocation");std::string tag="write-"+std::to_string(++write_seq);
 file(tag+"-before.bin",read(a,unsigned(b.size())));file(tag+"-adapter.bin",b);
 json("{\"kind\":\"write\",\"id\":"+std::to_string(write_seq)+",\"address\":"+std::to_string(a)+",\"length\":"+std::to_string(b.size())+",\"purpose\":\""+purpose+"\"}");
 for(unsigned i=0;i<b.size();++i)bus_write_u8_slow(a+i,b[i]);check(read(a,unsigned(b.size()))==b,"adapter write readback");
}
inline void capture(const std::string& tag){
 file(tag+"-context.bin",read(context,0xa350));file(tag+"-slot.bin",read(slot,0x370));file(tag+"-points.bin",read(points,0x4000));file(tag+"-descriptors.bin",read(descriptors,0x100));file(tag+"-stack.bin",read(arena,0x4000));file(tag+"-counts.bin",read(counts,0x100));
 file(tag+"-mainram.bin",read(0x02000000,0x400000));
}
template<class CPU> inline void record(CPU& c,const char* kind){
 std::string s="{\"kind\":\""+std::string(kind)+"\",\"stroke\":"+std::to_string(stroke)+",\"phase\":"+std::to_string(phase)+",\"cycle9\":"+std::to_string(g_runtime_cycles)+",\"min_sp\":"+std::to_string(min_sp)+",\"r\":[";
 for(unsigned i=0;i<16;++i)s+=(i?",":"")+std::to_string(c.R[i]);s+="],\"stack\":[";
 for(unsigned i=0;i<5;++i)s+=(i?",":"")+std::to_string(word(call_sp+4*i));
 s+="],\"counts\":["+std::to_string(word(counts))+","+std::to_string(word(counts+4))+"],\"candidate\":"+std::to_string(word(slot+0x104)&65535)+",\"metric\":"+std::to_string(word(slot+0x144))+"}";json(s);
}
template<class CPU> inline void invoke(CPU& c){
 std::vector<uint8_t> args;
 if(phase==0){write(counts,std::vector<uint8_t>(8,0),"output count initialization");for(uint32_t v:{16u,counts,slot+0x104,16u,counts+4})put32(args,v);write(call_sp,args,"recognition ABI stack");}
 c.R[0]=context;c.R[1]=phase==0?descriptors+8*stroke:1;c.R[2]=phase==0?stroke:0;c.R[3]=phase==0?slot+0xe4:slot+0x144;c.R[13]=call_sp;c.R[14]=0x02051af8;c.R[15]=phase==0?0x020a41a0:0x020a3fb8;c.cpsr.t=false;
 std::string tag="call-"+std::to_string(stroke)+"-"+std::to_string(phase);
 capture(tag+"-before");record(c,"entry");
}
// Fixed two-stroke experiment only. 0=normal instruction, 1=redirect, 2=terminal stop.
template<class CPU> inline int control(CPU& c){
 if(!root()||!*root()||g_nds_active!=NDS_ARM9||done)return 0;
 static std::optional<CPU> saved;
 try {
 if(!active){
  if(c.R[15]!=0x02026510u||c.cpsr.t)return 0;
  check(g_nds_force_tier3,"Task S requires force-tier3");
  exercise=c.R[0];check(ram(exercise,0xc34),"exercise pointer");manager=word(exercise+0xc24);check(ram(manager,0x238),"manager pointer");check(word(manager)==1,"slot count");slot=word(manager+4);check(ram(slot,0x370),"slot pointer");
  check(word(exercise+0x4c)==4&&word(exercise+0x44)==1&&(word(exercise+0x10)&65535)==1,"not preserved 11-7 checkpoint");
  check(word(slot+8)==0&&word(slot+0x214)==0&&word(slot+0x218)==0&&word(manager+0x230)==0,"recognition slot is not idle");
  context=word(slot+0x1c);points=word(slot+0x208);descriptors=word(slot+0x20c);arena=word(slot+0x1fc);counts=word(slot+0x200);
  struct Span{uint32_t p,n;};std::vector<Span> spans={{exercise,0xc34},{manager,0x238},{slot,0x370},{context,0xa350},{points,0x4000},{descriptors,0x100},{arena,0x4000},{counts,0x100}};
  for(unsigned i=0;i<spans.size();++i){check(ram(spans[i].p,spans[i].n),"allocation outside writable title heap");for(unsigned j=0;j<i;++j)check(uint64_t(spans[i].p)+spans[i].n<=spans[j].p||uint64_t(spans[j].p)+spans[j].n<=spans[i].p,"allocation overlap");}
  check(word(0x020a41a0)==0xe92d47f0u,"recognition target instruction mismatch");
  saved=c;exercise_before=read(exercise,0xc34);file("exercise-before.bin",exercise_before);file("manager-before.bin",read(manager,0x238));
  call_sp=(arena+0x4000-32)&~7u;min_sp=call_sp;start_cycles=g_runtime_cycles;
  json("{\"kind\":\"resolved\",\"exercise\":"+std::to_string(exercise)+",\"manager\":"+std::to_string(manager)+",\"slot\":"+std::to_string(slot)+",\"context\":"+std::to_string(context)+",\"points\":"+std::to_string(points)+",\"descriptors\":"+std::to_string(descriptors)+",\"arena\":"+std::to_string(arena)+",\"counts\":"+std::to_string(counts)+"}");
  capture("initial");const char* variant=std::getenv("NDS_TASK_S_VARIANT");check(variant&&(std::string(variant)=="A"||std::string(variant)=="B"),"variant must be A or B");auto enc=encode(source(std::string(variant)=="A"),points);write(points,enc.points,"adapter points");write(descriptors,enc.descriptors,"adapter descriptors");guard=std::vector<uint8_t>(256,0xa5);write(arena,guard,"stack lower guard");
  active=true;invoke(c);return 1;
 }
 check(g_runtime_cycles-start_cycles<50000000,"recognition diagnostic cycle bound");
 check(c.R[15]!=0x020266b4&&c.R[15]!=0x02025778&&c.R[15]!=0x02025698&&c.R[15]!=0x02052424,"forbidden exercise consumer/accumulator");
 if((c.cpsr.mode==saved->cpsr.mode)){check(c.R[13]>=arena+256&&c.R[13]<=arena+0x4000,"diagnostic stack bounds");min_sp=std::min(min_sp,c.R[13]);}
 if(c.R[15]!=0x02051af8u||c.cpsr.t)return 0;
 check(c.R[13]==call_sp,"return stack mismatch");check(read(arena,256)==guard,"stack guard overwritten");
 for(unsigned i=4;i<=11;++i)check(c.R[i]==saved->R[i],"callee-saved register mismatch");
 capture("call-"+std::to_string(stroke)+"-"+std::to_string(phase)+"-after");record(c,"return");check(c.R[0]==0,"target returned error");
 if(phase==0){phase=1;invoke(c);return 1;}
 if(stroke==0){stroke=1;phase=0;invoke(c);return 1;}
 check(read(exercise,0xc34)==exercise_before,"exercise object changed");file("exercise-after.bin",read(exercise,0xc34));file("manager-after.bin",read(manager,0x238));c=*saved;record(c,"stopped");done=true;active=false;nds_halt("Task S complete before exercise consumer");return 2;
 }catch(const std::exception& e){json("{\"kind\":\"error\",\"message\":\""+std::string(e.what())+"\"}");done=true;active=false;nds_halt("Task S diagnostic validation failed");return 2;}
}
}
