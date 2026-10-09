#include "adapter.h"
#include <cassert>
int main() {
 using namespace task_s;
 auto a=encode(source(true),0x02125cf4),b=encode(source(false),0x02125cf4);
 assert(a.points.size()==56&&b.points.size()==32&&a.descriptors.size()==16);
 auto rejected=[](const Strokes& s){try{encode(s,0x02125cf4);return false;}catch(const std::runtime_error&){return true;}};
 assert(rejected({})&&rejected({{}}));
 assert(rejected({{{256,10}}})&&rejected({{{1,192}}})&&rejected({{{-1,10}}}));
 assert(rejected(Strokes(33,Stroke{{1,1}})));
 assert(rejected(Strokes{Stroke(4097,Point{1,1})}));
 assert(encode(Strokes{Stroke(4096,Point{1,1})},0x02125cf4).points.size()==0x4000);
}
