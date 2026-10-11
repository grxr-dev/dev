#include "guard.h"
#include "../task_ab/guard.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>
int main(){
    using namespace task_ac_guard;
    const auto count=sizeof(decision_path)/sizeof(*decision_path);
    assert(count==46&&decision_path[41]==0x02025734&&decision_path[42]==0x02025738&&decision_path[43]==0x0202573c&&decision_path[44]==0x02025740&&decision_path[45]==0x02025744);
    for(size_t i=0;i<45;++i)assert(decision_path[i]==task_ab_guard::decision_path[i]);
    for(size_t i=0;i<count;++i){
        assert(permits(i,decision_path[i],i));
        assert(dispatches(i,decision_path[i],i)==(i<45));
        assert(!dispatches(i,decision_path[i],i+1));
        assert(!dispatches(i,0x02025744,i));
        for(auto forbidden:{0x02025748u,0x02025748u,0x020265d4u,0x020265e4u,0x020265f8u,0x0200de78u,0x02026be4u})assert(!permits(i,forbidden,i));
        if(i!=1)assert(!permits(i,0x02025778,i));
        if(i!=20)assert(!permits(i,0x02025698,i));
        if(i!=44)assert(!dispatches(i,0x02025740,i));
        if(i!=43)assert(!dispatches(i,0x0202573c,i));
        if(i!=42)assert(!dispatches(i,0x02025738,i));
    }
    assert(!permits(count,0x02025744,count)&&!permits(100,0x02025744,100));
    assert(bounded_second_store(0x05801504,0x020e9a00,1,true));
    for(auto bad:{0x15801504u,0x05901504u,0x05801508u,0x05c01504u,0x05a01504u})assert(!bounded_second_store(bad,0x020e9a00,1,true));
    assert(!bounded_second_store(0x05801504,0x020e9a04,1,true)&&!bounded_second_store(0x05801504,0x020e9a00,4,true)&&!bounded_second_store(0x05801504,0x020e9a00,1,false));
    assert(bounded_stack_adjust(0x028dd004,0x027e3b04,true));
    for(auto bad:{0x128dd004u,0x029dd004u,0x028dd008u,0x028de004u,0x024dd004u})assert(!bounded_stack_adjust(bad,0x027e3b04,true));
    assert(!bounded_stack_adjust(0x028dd004,0x027e3b08,true)&&!bounded_stack_adjust(0x028dd004,0x027e3b04,false));
    assert(correct(false,true,true,false,0));
    for(auto mismatch:{1u,4u})assert(!correct(false,true,true,false,mismatch));
    assert(!correct(false,false,true,false,0)&&!correct(true,true,true,false,0));
    assert(!correct(false,true,false,false,0)&&!correct(false,true,true,true,0));
    std::puts("PASS: Task AB prefix parity; exactly 45 dispatches; successor never dispatchable; fixed store/stack-adjust operands/decode; divergence, repeat, predicate, ordinal and downstream rejection");
}
