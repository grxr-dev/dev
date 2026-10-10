#include "bc_calculations_policy.h"
#include <cassert>
#include <iostream>
using namespace brainage_custom;
DigitResult output(const char* primary,const char* secondary,const char* prefix="",const char* prefix_secondary=""){
    DigitResult result;result.success=true;
    for(unsigned group=0;group<2;++group){const char* codes=group?primary:prefix;const char* alternate=group?secondary:prefix_secondary;auto& value=result.groups[group];
        while(*codes){auto index=value.code_count++;value.codes[index]=*codes++;value.accessor_codes[index]=*alternate++;}value.returned_count=value.code_count;}
    return result;
}
int main(){
    CalculationsPolicy known;
    auto first=known.consume(output("2","0"),4,1);assert(first.integer==2&&first.countdown==41&&first.timing_supported);
    auto second=known.consume(output("4","0"),4,2);assert(second.integer==4&&second.countdown==1&&second.timing_supported);
    assert(CalculationsPolicy().consume(output("4","0"),4,1).countdown==11);
    assert(CalculationsPolicy().consume(output("1","7"),7,1).integer==7);
    assert(CalculationsPolicy().consume(output("0","9"),9,1).countdown==1);
    assert(CalculationsPolicy().consume(output("7","1"),1,1).integer==7);
    assert(CalculationsPolicy().consume(output("23","49"),49,2).integer==49);
    assert(CalculationsPolicy().consume(output("23","19"),19,2).integer==23);
    CalculationsPolicy retained;assert(retained.consume(output("2","2","1","1"),12,1).integer==12);
    assert(retained.consume(output("3","3"),13,2).integer==13);
    assert(CalculationsPolicy().consume(output("123","123"),4,1).integer==0xffff);
    assert(CalculationsPolicy().consume(output("/","/"),4,1).integer==0xffff);
    assert(!CalculationsPolicy().consume(output("44","44"),44,3).timing_supported);
    auto invalid=output("4","0");invalid.groups[1].code_count=16;
    bool rejected=false;try{CalculationsPolicy().consume(invalid,4,2);}catch(const std::runtime_error&){rejected=true;}assert(rejected);
    std::cout<<"PASS: bounded groups/prefix, exact positional policy, 2 -> 4 timing, invalid sentinel and unsupported contributor timing\n";
}
