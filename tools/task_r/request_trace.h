#pragma once
#include <cstdio>
#include <cstdlib>
#include <algorithm>
#include "state.h"
namespace task_r {
inline uint32_t manager=0, exercise=0;
inline bool ram(uint32_t p, unsigned n) { return n && p>=0x02000000u && p<=0x02800000u-n; }
inline uint32_t word(uint32_t p) { uint32_t v=0; if(ram(p,4))for(unsigned i=0;i<4;++i)v|=uint32_t(bus_debug_read8(9,p+i))<<(8*i); return v; }
inline void snapshot(uint32_t pc,bool thumb,const uint32_t* r) {
 if(g_nds_active!=NDS_ARM9 || thumb)return;
 static FILE* f=[] {const char* p=std::getenv("NDS_TASK_R_TRACE");return p&&*p?std::fopen(p,"wb"):nullptr;}();
 if(!f)return;
 switch(pc) {
 case 0x02026510: exercise=r[0];break;
 case 0x02052424: manager=r[0];break;
 case 0x02052534:case 0x02052548:case 0x02052558:case 0x02052590:
 case 0x020525e4:case 0x020525f4:case 0x0205204c:case 0x020520b0:case 0x020520b4:
 case 0x02051a80:case 0x02051af4:case 0x02051af8:case 0x02051b28:case 0x02051b2c:
 case 0x02051b50:case 0x02051b54:case 0x02051b74:case 0x02051b78:
 case 0x02051c98:case 0x02051c9c:case 0x02051e4c:case 0x02051e50:
 case 0x02052030:case 0x02052038:case 0x0205274c:case 0x020527dc:
 case 0x02052904:case 0x02052938:case 0x02052fa4:case 0x02026690:
 case 0x020266b4:case 0x02025778:case 0x02025698:case 0x02025728:case 0x02025740:
 case 0x020265d4:case 0x020265f8:case 0x020269d4:
 case 0x020a41a0:case 0x020a4374:case 0x020a3fb8:case 0x020a3ffc:case 0x020a3f2c:
 case 0x020a437c:case 0x020a447c:break;
 default:return;
 }
 static unsigned seq=0;if(seq>=12000)return;
 std::fprintf(f,"{\"seq\":%u,\"pc\":%u,\"cycle9\":%llu,\"insn9\":%llu,\"manager\":%u,\"exercise\":%u,\"r\":[",++seq,pc,(unsigned long long)g_runtime_cycles,(unsigned long long)g_insn_count[NDS_ARM9],manager,exercise);
 for(unsigned i=0;i<16;++i)std::fprintf(f,"%s%u",i?",":"",r[i]);
 std::fputs("],\"mem\":[",f);bool comma=false;
 auto dump=[&](uint32_t a,unsigned n) {if(!ram(a,n))return;std::fprintf(f,"%s{\"addr\":%u,\"hex\":\"",comma?",":"",a);comma=true;for(unsigned i=0;i<n;++i)std::fprintf(f,"%02x",unsigned(bus_debug_read8(9,a+i)));std::fputs("\"}",f);};
 dump(0x020da4e4,8);dump(manager,0x238);dump(exercise,0x54);dump(exercise+0x500,0x28);
 uint32_t slots=word(manager+4),count=std::min(word(manager),2u);
 for(unsigned s=0;s<count;++s) {uint32_t a=slots+0x370*s;dump(a,0x370);dump(word(a+0x208),std::min(word(a+0x214),512u)*4);dump(word(a+0x20c),std::min(word(a+0x218)+1,32u)*8);}
 for(unsigned i: {0u,1u,2u,3u,13u})dump(r[i],128);
 std::fputs("]}\n",f);std::fflush(f);
}
}
