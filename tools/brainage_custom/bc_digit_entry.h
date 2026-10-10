#pragma once
#include "bc_contract.h"
namespace brainage_custom {
class DigitEntryProbe final : public Exercise {
public:
    static constexpr unsigned max_strokes=8, max_points=512;
private:
    DigitRecognizer* recognizer;
    decuma::Strokes strokes;
    decuma::Stroke current;
    ExerciseStatus state;
    enum class Contact {none, canvas, continuation, ignored};
    Contact contact=Contact::none;
    DigitResult result;
    bool failed=false;
    uint64_t init_us=0;
    unsigned total_points=0;
    static bool canvas(uint16_t x,uint16_t y){return x>=24&&x<=232&&y>=32&&y<=136;}
    static bool continuation(uint16_t x,uint16_t y){return x>=72&&x<=184&&y>=148&&y<=184;}
    bool append(uint16_t x,uint16_t y){
        if(!canvas(x,y))return false;
        if(!current.empty()&&current.back().x==x&&current.back().y==y)return false;
        if(total_points>=max_points){failed=true;state.phase="error";return true;}
        current.push_back({int(x),int(y)});++total_points;return true;
    }
    void ready(){state.completed=failed||!strokes.empty();state.can_continue=state.completed&&!state.contact_down;}
public:
    explicit DigitEntryProbe(ExerciseServices& services):recognizer(services.digit_recognizer){}
    void begin() override {
        state={};state.phase="waiting";strokes.clear();current.clear();contact=Contact::none;failed=false;total_points=0;
        result=recognizer?recognizer->begin_session():DigitResult{false,false,0,0,1,0,0,"recognizer unavailable"};
        init_us=result.wall_us;failed=!result.success;if(failed)state.phase="error";ready();
    }
    ExerciseStatus status() const override {
        auto copy=state;copy.diagnostics={{"completed_strokes",strokes.size()},{"point_count",total_points},{"current_points",current.size()},
            {"candidate",result.candidate_available?uint64_t(result.candidate):0u},{"candidate_available",result.candidate_available},{"recognition_return",result.error},{"recognition_success",result.success},
            {"metric",result.metric},{"init_wall_us",init_us},{"call_wall_us",result.wall_us},{"private_instructions",result.instructions},{"recognition_error",failed}};return copy;
    }
    ExerciseEvent touch(uint16_t x,uint16_t y,bool down) override {
        if(down){
            if(!state.contact_down){state.contact_down=true;contact=Contact::ignored;
                if(continuation(x,y))contact=Contact::continuation;
                else if(canvas(x,y)&&!failed&&strokes.size()<max_strokes){contact=Contact::canvas;current.clear();}}
            else if(contact==Contact::continuation&&!continuation(x,y))contact=Contact::ignored;
            bool changed=contact==Contact::canvas&&append(x,y);ready();return {true,changed,false,contact==Contact::continuation?1u:0u,0};
        }
        if(!state.contact_down)return {};
        state.contact_down=false;const auto released=contact;contact=Contact::none;
        if(released==Contact::canvas){
            strokes.push_back(std::move(current));current.clear();
            if(!failed){result=recognizer->recognize_stroke(strokes.back());failed=!result.success;}
            if(failed){result.candidate_available=false;result.candidate=0;state.phase="error";}
            else state.phase=result.candidate_available?"candidate":"no_candidate";
            ready();return {true,true,false,0,0};
        }
        ready();
        if(released==Contact::continuation&&state.can_continue){state.phase="resuming";return {true,false,true,1,0};}
        return {false,false,false,released==Contact::continuation?1u:0u,0};
    }
    void render(Surface& surface) const override {
        surface.pixels.fill(0xff172335u);
        surface.text(77,3,"DIGIT ENTRY TEST",0xffedf4ffu);
        surface.text(92,14,"DRAW A DIGIT",0xffb8c6dcu);
        surface.text(74,23,failed?"RECOGNITION ERROR":result.candidate_available?"CANDIDATE: "+std::string(1,char(result.candidate)):strokes.empty()?"WAITING":"NO CANDIDATE YET",0xffedf4ffu);
        surface.rectangle(23,31,233,137,0xff93a8c5u);surface.rectangle(24,32,232,136,0xffedf4ffu);
        const auto paint=[&](const decuma::Stroke& stroke){for(size_t i=0;i<stroke.size();++i){auto a=stroke[i?i-1:0],b=stroke[i];surface.line(a.x,a.y,b.x,b.y,0xff15283fu);}};
        for(const auto& stroke:strokes)paint(stroke);
        paint(current);
        surface.rectangle(72,148,184,184,state.can_continue?0xff42d39fu:0xff47566bu);
        surface.rectangle(73,149,183,183,0xff24354cu);
        surface.text(80,160,"CONTINUE",state.can_continue?0xffedf4ffu:0xff78879bu,2);
    }
};
}
