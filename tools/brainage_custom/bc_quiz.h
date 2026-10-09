#pragma once

#include <cstring>
#include "bc_contract.h"

namespace brainage_custom {
class ArithmeticQuiz final : public Exercise {
    ExerciseStatus state{};
    unsigned pressed = 0;

    static unsigned target(uint16_t x, uint16_t y) {
        if (y >= 96 && y <= 136) {
            if (x >= 24 && x <= 84) return 3;
            if (x >= 98 && x <= 158) return 4;
            if (x >= 172 && x <= 232) return 5;
        }
        return x >= 72 && x <= 184 && y >= 148 && y <= 184 ? 1 : 0;
    }

    ExerciseEvent select(unsigned value) {
        if (value == 1 && state.can_continue && !state.contact_down) {
            state.phase = "resuming";
            state.can_continue = false;
            return {true, false, true, value, 0};
        }
        if (state.completed || (value != 3 && value != 4 && value != 5)) return {false, false, false, value, 0};
        state.answers.push_back(value);
        state.completed = value == 4;
        state.can_continue = state.completed;
        state.phase = state.completed ? "completed" : "incorrect";
        return {true, true, false, value, value};
    }

public:
    void begin() override {
        state = {};
        state.phase = "question";
        pressed = 0;
    }

    ExerciseStatus status() const override { return state; }

    ExerciseEvent touch(uint16_t x, uint16_t y, bool down) override {
        const unsigned hit = target(x, y);
        if (down) {
            if (!state.contact_down) pressed = hit;
            else if (hit != pressed) pressed = 0;
            state.contact_down = true;
            return {true, false, false, hit, 0};
        }
        const unsigned released = state.contact_down ? pressed : 0;
        state.contact_down = false;
        pressed = 0;
        return released ? select(released) : ExerciseEvent{};
    }

    ExerciseEvent diagnostic_action(const char* action, unsigned value) override {
        if (state.contact_down) return {};
        if (std::strcmp(action, "choose") == 0) return select(value);
        if (std::strcmp(action, "continue") == 0) return select(1);
        return {};
    }

    void render(Surface& surface) const override {
        surface.pixels.fill(0xff172335u);
        surface.text(20, 14, "BRAIN AGE NATIVE EXERCISE", 0xffedf4ffu);
        surface.text(74, 36, "2 + 2 = ?", 0xffedf4ffu, 2);
        const uint32_t result = state.completed ? 0xff42d39fu : 0xffff8795u;
        surface.text(78, 62, state.completed ? "CORRECT" : state.answers.empty() ? "CHOOSE" : "INCORRECT",
            state.answers.empty() ? 0xffedf4ffu : result);
        surface.text(86, 78, "ATTEMPTS " + std::to_string(state.answers.size()), 0xffb8c6dcu);
        for (unsigned index = 0; index < 3; ++index) {
            const unsigned left = 24 + index * 74;
            surface.rectangle(left, 96, left + 60, 136, 0xff93a8c5u);
            surface.rectangle(left + 1, 97, left + 59, 135, 0xff30445eu);
            surface.text(left + 23, 106, std::to_string(index + 3), state.completed ? 0xff78879bu : 0xffedf4ffu, 3);
        }
        surface.rectangle(72, 148, 184, 184, state.can_continue ? 0xff42d39fu : 0xff47566bu);
        surface.rectangle(73, 149, 183, 183, 0xff24354cu);
        surface.text(80, 160, "CONTINUE", state.can_continue ? 0xffedf4ffu : 0xff78879bu, 2);
    }
};
}
