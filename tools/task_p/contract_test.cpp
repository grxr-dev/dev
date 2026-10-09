#include <cassert>
#include <cstring>
#include <cstdio>
#include "bc_activation.h"
#include "bc_catalog.h"
#include "../task_l/mini_exercise_state.h"
#include "../task_n/native_surface.h"

struct ContractMock final : brainage_custom::Exercise {
    brainage_custom::ExerciseStatus state{};
    void begin() override { state = {}; state.phase = "mock"; }
    void render(brainage_custom::Surface& surface) const override { surface.pixels.fill(0xff123456u); }
    brainage_custom::ExerciseEvent touch(uint16_t, uint16_t, bool down) override {
        state.contact_down = down;
        state.completed = !down;
        state.can_continue = !down;
        return {true, true, false, 0, 0};
    }
    brainage_custom::ExerciseStatus status() const override { return state; }
};

int main(int argc, char** argv) {
    using namespace brainage_custom;
    if (argc == 2 && std::strcmp(argv[1], "--activation") == 0) {
        const auto configuration = activation_from_environment();
        std::printf("%u %u\n", unsigned(configuration.enabled), unsigned(configuration.presentation));
        return 0;
    }
    assert(!activation(nullptr, nullptr, nullptr, nullptr).enabled);
    assert(!activation("0", "1", "1", "1").enabled);
    assert(activation(nullptr, "1", nullptr, "1").presentation);
    assert(activation(nullptr, "1", nullptr, nullptr).enabled);
    assert(!activation(nullptr, "1", nullptr, nullptr).presentation);
    assert(activation("1", nullptr, nullptr, nullptr).presentation);
    assert(!activation("1", "1", "0", "1").presentation);
    assert(activation("1", "0", "1", "0").enabled);
    const auto& descriptor = launch_exercise();
    assert(std::strcmp(descriptor.id, "arithmetic-2plus2") == 0);
    auto exercise = descriptor.create();
    exercise->begin();
    Surface actual;
    brainage_native::NativeSurface reference;
    brainage_native::MiniExercise historical;
    exercise->render(actual);
    reference.paint(historical);
    assert(actual.pixels == reference.pixels);
    const auto tap = [&](unsigned x, unsigned y) {
        exercise->touch(x, y, true);
        assert(exercise->status().contact_down);
        const auto result = exercise->touch(0, 0, false);
        assert(!exercise->status().contact_down);
        return result;
    };
    assert(!tap(128, 166).request_exit);
    for (const auto answer : {3u, 5u, 4u}) {
        const unsigned x = answer == 3 ? 54 : answer == 5 ? 202 : 128;
        const auto result = tap(x, 116);
        assert(result.accepted && result.selected == answer && !result.request_exit);
        assert(historical.choose(answer));
        exercise->render(actual);
        reference.paint(historical);
        assert(actual.pixels == reference.pixels);
    }
    assert(exercise->status().completed && exercise->status().can_continue);
    assert(tap(128, 166).request_exit);
    assert(!tap(128, 166).request_exit);
    exercise->begin();
    assert(exercise->status().answers.empty() && !exercise->status().completed);
    assert(exercise->diagnostic_action("choose", 4).accepted);
    assert(exercise->diagnostic_action("continue", 0).request_exit);
    exercise.reset();
    std::unique_ptr<Exercise> mock = std::make_unique<ContractMock>();
    mock->begin();
    mock->render(actual);
    assert(actual.pixels[0] == 0xff123456u);
    mock->touch(12, 34, true);
    mock->touch(0, 0, false);
    assert(mock->status().can_continue);
    std::puts("PASS: activation aliases/precedence, unchanged quiz pixels, touch/exit contract and non-quiz mock");
}
