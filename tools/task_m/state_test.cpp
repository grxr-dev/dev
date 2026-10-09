#include <cassert>
#include <initializer_list>
#include "touch_state.h"

int main() {
    using namespace brainage_native;
    TouchContact contact;
    for (unsigned target : {3u, 4u, 5u, 1u}) {
        const uint16_t x = target == 3 ? 54 : target == 5 ? 202 : 128;
        const uint16_t y = target == 1 ? 166 : 116;
        assert(contact.receive(x, y, true) == 0 && contact.down);
        assert(contact.receive(x, y, true) == 0);
        assert(contact.receive(x, y, false) == target && !contact.down);
        assert(contact.receive(x, y, false) == 0);
    }
    assert(contact.receive(54, 116, true) == 0);
    assert(contact.receive(202, 116, true) == 0);
    assert(contact.receive(202, 116, false) == 0);
    assert(touch_target(0, 0) == 0);
    assert(touch_target(24, 96) == 3 && touch_target(84, 136) == 3);
    assert(touch_target(85, 136) == 0 && touch_target(72, 184) == 1);
}
