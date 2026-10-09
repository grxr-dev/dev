#pragma once

#include <cstdint>

namespace brainage_native {
inline unsigned touch_target(uint16_t x, uint16_t y) {
    if (y >= 96 && y <= 136) {
        if (x >= 24 && x <= 84) return 3;
        if (x >= 98 && x <= 158) return 4;
        if (x >= 172 && x <= 232) return 5;
    }
    return x >= 72 && x <= 184 && y >= 148 && y <= 184 ? 1 : 0;
}

struct TouchContact {
    bool down = false;
    unsigned pressed = 0;
    unsigned receive(uint16_t x, uint16_t y, bool contact) {
        const unsigned target = touch_target(x, y);
        if (contact) {
            if (!down) pressed = target;
            else if (target != pressed) pressed = 0;
            down = true;
            return 0;
        }
        const unsigned released = down ? pressed : 0;
        down = false;
        pressed = 0;
        return released;
    }
};
}
