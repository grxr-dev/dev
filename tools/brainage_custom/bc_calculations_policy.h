#pragma once
#include "bc_digit_recognizer.h"
#include <stdexcept>
#include <vector>
namespace brainage_custom {
struct CalculationsSelection {
    std::vector<uint16_t> primary, secondary, chosen;
    uint16_t integer=0xffff;
    unsigned countdown=0;
    bool timing_supported=false;
};
class CalculationsPolicy {
    std::vector<uint16_t> prefix, prefix_secondary;
    static void check(bool valid){if(!valid)throw std::runtime_error("invalid bounded numeric output");}
public:
    CalculationsSelection consume(const DigitResult& result,int expected,unsigned released_strokes){
        check(result.success&&expected>=0&&expected<=99&&released_strokes>0);
        for(const auto& group:result.groups){
            check(group.returned_count<=16&&group.code_count<=15&&group.codes[group.code_count]==0);
            for(unsigned index=0;index<group.code_count;++index)check(group.codes[index]!=0);
        }
        const auto& delta=result.groups[0];
        check(prefix.size()+delta.code_count<=16);
        for(unsigned index=0;index<delta.code_count;++index){prefix.push_back(delta.codes[index]);prefix_secondary.push_back(delta.accessor_codes[index]);}
        CalculationsSelection selection;
        selection.primary=prefix;selection.secondary=prefix_secondary;
        const auto& suffix=result.groups[1];
        for(unsigned index=0;index<suffix.code_count&&selection.primary.size()<16;++index){selection.primary.push_back(suffix.codes[index]);selection.secondary.push_back(suffix.accessor_codes[index]);}
        selection.chosen=selection.primary;
        if(expected<10&&selection.primary.size()==1&&selection.secondary[0]==48+expected&&selection.secondary[0]!=49)selection.chosen[0]=selection.secondary[0];
        if(expected>=10&&selection.primary.size()==2){
            if(selection.secondary[0]==48+expected/10&&selection.secondary[0]!=49)selection.chosen[0]=selection.secondary[0];
            if(selection.secondary[1]==48+expected%10&&selection.secondary[0]!=49)selection.chosen[1]=selection.secondary[1];
        }
        uint32_t integer=0;
        for(auto code:selection.chosen)integer=integer*10u+uint32_t(int(code)-48);
        if(int32_t(integer)>=0&&int32_t(integer)<100)selection.integer=uint16_t(integer);
        selection.countdown=1;selection.timing_supported=true;
        if(selection.integer!=expected){if(selection.integer!=0xffff)selection.countdown=41;}
        else if(expected%10==4||expected%10==5){
            if(released_strokes==1||(released_strokes==2&&expected>=10))selection.countdown=11;
            if(released_strokes==3&&expected>=10)selection.timing_supported=false;
        }
        if(selection.countdown>1&&expected>=10&&expected%10!=4&&expected%10!=5&&expected%10!=7)selection.countdown=1;
        return selection;
    }
};
}
