#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <io.h>
#include <sys/stat.h>
#include "../task_aw/bridge.h"

constexpr unsigned NDS_ARM9=0;
unsigned g_nds_active=0;
uint64_t g_runtime_cycles=3416875777ULL, g_cycle_cap=3416875778ULL;
uint16_t g_divcnt=0x8001, g_sqrtcnt=0;
uint32_t g_div_numer[2]={0,4096}, g_div_denom[2]={4096,0};
uint32_t g_div_quot[2]={0,1}, g_div_rem[2]={0,0};
uint32_t g_sqrt_res=0, g_sqrt_val[2]={0,0};
#include "source.inc"

unsigned checks=0;
void check(bool value) {
    ++checks;
    if (!value) std::exit(1);
}
void persistence() { std::fputs("PERSISTENCE_SENTINEL",stderr); }
struct Shutdown {
    ~Shutdown() { std::fputs("SHUTDOWN_SENTINEL",stderr); }
};
int main(int argc,char** argv) {
    Shutdown shutdown;
    if (argc==3) {
        std::atexit(persistence);
        const int descriptor=_open(argv[2],_O_CREAT|_O_EXCL|_O_WRONLY|_O_BINARY,_S_IREAD|_S_IWRITE);
        FILE* output=descriptor<0 ? nullptr : _fdopen(descriptor,"wb");
        if (!output) return 2;
        const bool success=std::strcmp(argv[1],"success")==0;
        std::fprintf(output,"{\"event\":\"%s\",\"guest_instructions\":0}\n",success ? "negative_certificate" : "failure");
        task_aw::dispose(output,success ? 73 : 79);
        std::fputs("SCHEDULER_DEVICE_IRQ_ARM7_GUEST_SENTINEL",stderr);
        return 3;
    }
    check(!task_aw::enabled());
    check(!nds_slice_over());
    check(active_system_timestamp()==1708437888ULL);
    check(math_reg_read32(0x04000280)==0x8001);
    check(g_divcnt==0x8001);
    check(g_div_numer[1]==4096 && g_div_denom[0]==4096);
    check(g_div_quot[1]==1 && g_div_rem[0]==0);
    const auto cost=arm9_cycle_combine(1,8,0,1);
    check(cost==8);
    check(g_runtime_cycles+cost==3416875785ULL);
    check(g_runtime_cycles+cost>g_cycle_cap);
    for (uint64_t margin=0;margin<=10;++margin) {
        g_runtime_cycles=3416875777ULL;
        g_cycle_cap=g_runtime_cycles+margin;
        check(bool(nds_slice_over())==(margin==0));
        check((g_runtime_cycles+cost<g_cycle_cap)==(margin>8));
    }
    g_runtime_cycles=3416875778ULL;
    g_cycle_cap=3416875778ULL;
    check(nds_slice_over());
    g_runtime_cycles=3416875785ULL;
    check(nds_slice_over());
    check(active_system_timestamp()==1708437892ULL);
    check(math_reg_read32(0x04000280)==0x8001);
    g_nds_active=1;
    check(active_system_timestamp()==g_runtime_cycles);
    check(!task_aw::enabled());
    std::printf("{\"checks\":%u,\"guest_instructions\":0,\"runtime_MMIO\":0}\n",checks);
    std::fflush(stdout);
    return 0;
}
