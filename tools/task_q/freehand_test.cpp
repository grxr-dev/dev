#include <cassert>
#include <cstdio>
#include <cstring>
#include <limits>
#include "bc_catalog.h"

uint64_t metric(const brainage_custom::ExerciseStatus& state, const char* name) {
    for (const auto& item : state.diagnostics) if (item.name == name) return item.value;
    assert(false);
    return 0;
}

int main(int argc, char** argv) {
    using namespace brainage_custom;
    if (argc == 2 && std::strcmp(argv[1], "--selection") == 0) {
        try { std::puts(launch_exercise().id); return 0; }
        catch (const std::runtime_error& error) { std::puts(error.what()); return 2; }
    }
    Surface surface;
    const uint32_t color = 0xff123456u;
    surface.line(10, 12, 15, 12, color);
    for (unsigned column = 10; column <= 15; ++column) assert(surface.pixels[12 * 256 + column] == color);
    surface.line(20, 10, 20, 15, color);
    for (unsigned row = 10; row <= 15; ++row) assert(surface.pixels[row * 256 + 20] == color);
    surface.line(30, 30, 35, 35, color);
    surface.line(40, 35, 45, 30, color);
    for (unsigned delta = 0; delta <= 5; ++delta) {
        assert(surface.pixels[(30 + delta) * 256 + 30 + delta] == color);
        assert(surface.pixels[(35 - delta) * 256 + 40 + delta] == color);
    }
    surface.line(255, 191, 255, 191, color);
    assert(surface.pixels.back() == color);
    const auto before = surface.pixels;
    surface.line(-1, 0, 10, 0, color);
    surface.line(0, 0, 256, 0, color);
    surface.line(0, 0, 0, 192, color);
    surface.line(std::numeric_limits<int>::min(), 0, std::numeric_limits<int>::max(), 0, color);
    assert(surface.pixels == before);
    assert(std::strcmp(exercise_descriptor(nullptr).id, "arithmetic-2plus2") == 0);
    assert(std::strcmp(exercise_descriptor("").id, "arithmetic-2plus2") == 0);
    bool rejected = false;
    try { exercise_descriptor("unknown"); } catch (const std::runtime_error&) { rejected = true; }
    assert(rejected);
    auto exercise = exercise_descriptor("freehand-canvas").create();
    exercise->begin();
    const unsigned gesture[2][5][2] = {{{64,48},{96,72},{128,96},{160,120},{192,132}},
                                      {{192,48},{160,72},{128,96},{96,120},{64,132}}};
    for (unsigned stroke = 0; stroke < 2; ++stroke) {
        for (unsigned point = 0; point < 5; ++point) {
            exercise->touch(gesture[stroke][point][0], gesture[stroke][point][1], true);
            const auto state = exercise->status();
            assert(state.contact_down && metric(state, "completed_strokes") == stroke);
            assert(metric(state, "current_points") == point + 1);
        }
        exercise->touch(0, 0, false);
        assert(!exercise->touch(0, 0, false).accepted);
        const auto state = exercise->status();
        assert(!state.contact_down && metric(state, "completed_strokes") == stroke + 1);
        assert(metric(state, "point_count") == 5 * (stroke + 1));
        assert(state.can_continue == (stroke == 1));
        if (!stroke) {
            exercise->touch(128, 166, true);
            assert(!exercise->touch(0, 0, false).request_exit);
            assert(metric(exercise->status(), "point_count") == 5);
        }
    }
    exercise->render(surface);
    for (const auto& point : {std::array<unsigned,2>{80,60}, {112,84}, {144,108}, {176,126}, {176,60}, {144,84}})
        assert(surface.pixels[point[1] * 256 + point[0]] == FreehandCanvas::ink);
    exercise->touch(128, 166, true);
    assert(exercise->touch(0, 0, false).request_exit);
    exercise->touch(128, 166, true);
    assert(!exercise->touch(0, 0, false).request_exit);
    exercise->begin();
    exercise->touch(0, 0, true);
    exercise->touch(64, 48, true);
    exercise->touch(0, 0, false);
    assert(metric(exercise->status(), "point_count") == 0);
    exercise->touch(64, 48, true);
    exercise->touch(0, 0, true);
    exercise->touch(64, 48, true);
    exercise->touch(0, 0, false);
    assert(metric(exercise->status(), "point_count") == 1);
    exercise->begin();
    for (unsigned point = 0; point < FreehandCanvas::max_points + 50; ++point)
        exercise->touch(point % 2 ? 64 : 65, 48, true);
    exercise->touch(0, 0, false);
    exercise->touch(100, 100, true);
    exercise->touch(0, 0, false);
    assert(metric(exercise->status(), "point_count") == FreehandCanvas::max_points);
    assert(metric(exercise->status(), "completed_strokes") == 1 && metric(exercise->status(), "storage_limited"));
    exercise->begin();
    for (unsigned stroke = 0; stroke < FreehandCanvas::max_strokes + 20; ++stroke) {
        exercise->touch(64, 48, true);
        exercise->touch(0, 0, false);
    }
    assert(metric(exercise->status(), "completed_strokes") == FreehandCanvas::max_strokes);
    assert(metric(exercise->status(), "point_count") == FreehandCanvas::max_strokes);
    assert(metric(exercise->status(), "storage_limited"));
    std::puts("PASS: line endpoints/bounds/interpolation, two strokes, motion/release, exit and bounded storage");
}
