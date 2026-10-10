#include "guard.h"
#include "../task_aa/guard.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>
int main(){
    using namespace task_ab_guard;
    const auto count=sizeof(decision_path)/sizeof(*decision_path);
    assert(count==45&&decision_path[41]==0x02025734&&decision_path[42]==0x02025738&&decision_path[43]==0x0202573c&&decision_path[44]==0x02025740);
    for(size_t i=0;i<44;++i)assert(decision_path[i]==task_aa_guard::decision_path[i]);
    for(size_t i=0;i<count;++i){
        assert(permits(i,decision_path[i],i));
        assert(dispatches(i,decision_path[i],i)==(i<44));
        assert(!dispatches(i,decision_path[i],i+1));
        assert(!dispatches(i,0x02025740,i));
        for(auto forbidden:{0x02025744u,0x02025748u,0x020265d4u,0x020265e4u,0x020265f8u,0x0200de78u,0x02026be4u})assert(!permits(i,forbidden,i));
        if(i!=1)assert(!permits(i,0x02025778,i));
        if(i!=20)assert(!permits(i,0x02025698,i));
        if(i!=43)assert(!dispatches(i,0x0202573c,i));
        if(i!=42)assert(!dispatches(i,0x02025738,i));
    }
    assert(!permits(count,0x02025740,count)&&!permits(100,0x02025740,100));
    assert(bounded_second_store(0x05801504,0x020e9a00,1,true));
    for(auto bad:{0x15801504u,0x05901504u,0x05801508u,0x05c01504u,0x05a01504u})assert(!bounded_second_store(bad,0x020e9a00,1,true));
    assert(!bounded_second_store(0x05801504,0x020e9a04,1,true)&&!bounded_second_store(0x05801504,0x020e9a00,4,true)&&!bounded_second_store(0x05801504,0x020e9a00,1,false));
    assert(correct(false,true,true,false,0));
    for(auto mismatch:{1u,4u})assert(!correct(false,true,true,false,mismatch));
    assert(!correct(false,false,true,false,0)&&!correct(true,true,true,false,0));
    assert(!correct(false,true,false,false,0)&&!correct(false,true,true,true,0));
    std::puts("PASS: Task AA prefix parity; exactly 44 dispatches; successor never dispatchable; fixed store operands/decode; divergence, repeat, predicate, ordinal and downstream rejection");
}
