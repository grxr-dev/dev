// Encoding copied from Task S; parity is tested against the historical adapter.
#pragma once
#include <cstdint>
#include <vector>
#include <stdexcept>
namespace brainage_custom::decuma {
struct Point { int x,y; };
using Stroke=std::vector<Point>;
using Strokes=std::vector<Stroke>;
inline void put32(std::vector<uint8_t>& b,uint32_t v) {for(unsigned i=0;i<4;++i)b.push_back(uint8_t(v>>(8*i)));}
struct Encoded {std::vector<uint8_t> points,descriptors;};
inline Encoded encode(const Strokes& strokes,uint32_t guest_points) {
 if(strokes.empty()||strokes.size()>32)throw std::runtime_error("stroke capacity");
 if(uint64_t(guest_points)+0x4000>0x100000000ull)throw std::runtime_error("point address overflow");
 Encoded out;
 for(const auto& stroke:strokes) {
  if(stroke.empty()||out.points.size()/4+stroke.size()>4096)throw std::runtime_error("point capacity");
  put32(out.descriptors,uint32_t(stroke.size()));put32(out.descriptors,guest_points+uint32_t(out.points.size()));
  for(auto p:stroke) {if(p.x<0||p.x>255||p.y<0||p.y>191)throw std::runtime_error("DS coordinate bounds");
   uint16_t x=uint16_t(p.y),y=uint16_t(255-p.x);out.points.insert(out.points.end(),{uint8_t(x),uint8_t(x>>8),uint8_t(y),uint8_t(y>>8)});
  }
 }
 return out;
}
}
