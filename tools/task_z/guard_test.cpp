#include "guard.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>
int main(){
    using namespace task_z_guard;
    const auto count=sizeof(decision_path)/sizeof(*decision_path);
    assert(count==42&&decision_path[count-1]==0x02025734);
    for(size_t i=0;i<count;++i){
        assert(permits(i,decision_path[i],i));
        assert(!permits(i,decision_path[i],i+1));
        for(auto forbidden:{0x02025738u,0x0202573cu,0x02025748u,0x020265d4u,0x020265e4u,0x020265f8u,0x0200de78u,0x02026be4u})assert(!permits(i,forbidden,i));
        if(i!=1)assert(!permits(i,0x02025778,i));
        if(i!=20)assert(!permits(i,0x02025698,i));
    }
    assert(!permits(count,0x02025738,count));
    assert(!permits(100,0x02025734,100));
    assert(correct(false,true,true,false,0));
    assert(!correct(false,false,true,false,1));
    assert(!correct(false,true,true,false,1));
    assert(!correct(true,true,true,false,0));
    assert(!correct(false,true,false,false,0));
    assert(!correct(false,true,true,true,0));
    std::puts("PASS: exact sequence, repeated-entry, wrong-path, acceptance/progression/save/budget rejection and correct predicate");
}
