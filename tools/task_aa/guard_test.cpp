#include "guard.h"
#include "../task_z/guard.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>
int main(){
    using namespace task_aa_guard;
    const auto count=sizeof(decision_path)/sizeof(*decision_path);
    assert(count==44&&decision_path[41]==0x02025734&&decision_path[42]==0x02025738&&decision_path[43]==0x0202573c);
    for(size_t i=0;i<42;++i)assert(decision_path[i]==task_z_guard::decision_path[i]);
    for(size_t i=0;i<count;++i){
        assert(permits(i,decision_path[i],i));
        assert(dispatches(i,decision_path[i],i)==(i<43));
        assert(!dispatches(i,decision_path[i],i+1));
        assert(!dispatches(i,0x0202573c,i));
        for(auto forbidden:{0x02025740u,0x02025748u,0x020265d4u,0x020265e4u,0x020265f8u,0x0200de78u,0x02026be4u})assert(!permits(i,forbidden,i));
        if(i!=1)assert(!permits(i,0x02025778,i));
        if(i!=20)assert(!permits(i,0x02025698,i));
        if(i!=42)assert(!dispatches(i,0x02025738,i));
    }
    assert(!permits(count,0x0202573c,count)&&!permits(100,0x0202573c,100));
    assert(correct(false,true,true,false,0));
    for(auto mismatch:{1u,4u})assert(!correct(false,true,true,false,mismatch));
    assert(!correct(false,false,true,false,0)&&!correct(true,true,true,false,0));
    assert(!correct(false,true,false,false,0)&&!correct(false,true,true,true,0));
    std::puts("PASS: Task Z prefix parity; exactly 43 dispatches; second store never dispatchable; divergence, repeat, predicate, ordinal and downstream rejection");
}
