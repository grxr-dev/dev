#pragma once
#include <cstddef>
#include <cstdint>
namespace task_z_guard {
inline constexpr uint32_t decision_path[]={
    0x020266b4,
    0x02025778,0x0202577c,0x02025780,0x02025784,0x02025788,0x0202578c,0x02025790,0x02025794,
    0x020257ac,0x020257b0,0x020257b4,0x020257b8,
    0x02025814,0x02025818,0x0202581c,0x02025820,0x02025824,0x02025828,0x0202582c,
    0x02025698,0x0202569c,0x020256a0,0x020256a4,0x020256a8,0x020256ac,0x020256b0,0x020256b4,0x020256b8,0x020256bc,
    0x02025708,0x0202570c,0x02025710,0x02025714,0x02025718,0x0202571c,0x02025720,0x02025724,0x02025728,0x0202572c,0x02025730,0x02025734
};
inline constexpr bool permits(size_t index,uint32_t pc,uint64_t instructions){
    return index<sizeof(decision_path)/sizeof(*decision_path)&&index<64&&instructions==index&&pc==decision_path[index];
}
inline constexpr bool correct(bool n,bool z,bool c,bool v,uint32_t mismatch){return !n&&z&&c&&!v&&mismatch==0;}
}
