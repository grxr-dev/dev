#include <cassert>
#include "native_surface.h"
#include "touch_state.h"

int main() {
    using namespace brainage_native;
    MiniExercise exercise;
    NativeSurface surface;
    for (char character : std::string("BRAINAGENATIVEEXERCISECHOOSEINCORRECTATTEMPTSCONTINUE012345+=?"))
        assert((NativeSurface::glyph(character) != std::array<uint8_t, 7>{}));
    surface.paint(exercise);
    const auto initial = surface.pixels;
    for (unsigned index = 0; index < 3; ++index) {
        const unsigned left = 24 + index * 74;
        assert(touch_target(left, 96) == index + 3);
        assert(surface.pixels[96 * 256 + left] == 0xff93a8c5u);
        assert(surface.pixels[136 * 256 + left + 60] == 0xff93a8c5u);
    }
    assert(surface.pixels[148 * 256 + 72] == 0xff47566bu);
    assert(exercise.choose(3));
    surface.paint(exercise);
    const auto incorrect = surface.pixels;
    assert(incorrect != initial);
    assert(exercise.choose(4));
    surface.paint(exercise);
    assert(surface.pixels != initial && surface.pixels != incorrect);
    assert(surface.pixels[148 * 256 + 72] == 0xff42d39fu);
}
