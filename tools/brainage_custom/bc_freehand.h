#pragma once

#include <array>
#include "bc_contract.h"

namespace brainage_custom {
class FreehandCanvas final : public Exercise {
public:
    static constexpr unsigned max_strokes = 8, max_points = 256;
    static constexpr uint32_t ink = 0xff15283fu;

private:
    struct Point { uint16_t x, y; };
    struct Stroke { unsigned start = 0, count = 0; };
    enum class Contact { none, canvas, continuation, ignored };
    std::array<Point, max_points> points{};
    std::array<Stroke, max_strokes> strokes{};
    ExerciseStatus state{};
    Contact contact = Contact::none;
    unsigned completed_strokes = 0, point_count = 0;
    bool limited = false;

    static bool in_canvas(uint16_t x, uint16_t y) {
        return x >= 24 && x <= 232 && y >= 32 && y <= 136;
    }

    static bool in_continue(uint16_t x, uint16_t y) {
        return x >= 72 && x <= 184 && y >= 148 && y <= 184;
    }

    bool append(uint16_t x, uint16_t y) {
        if (!in_canvas(x, y)) return false;
        auto& stroke = strokes[completed_strokes];
        if (stroke.count && points[point_count - 1].x == x && points[point_count - 1].y == y) return false;
        if (point_count == max_points) { limited = true; return false; }
        points[point_count++] = {x, y};
        ++stroke.count;
        return true;
    }

public:
    void begin() override {
        points = {};
        strokes = {};
        state = {};
        state.phase = "empty";
        contact = Contact::none;
        completed_strokes = point_count = 0;
        limited = false;
    }

    ExerciseStatus status() const override {
        auto snapshot = state;
        uint32_t hash = 2166136261u;
        const unsigned stored = completed_strokes + (contact == Contact::canvas ? 1 : 0);
        for (unsigned index = 0; index < stored; ++index) {
            hash = (hash ^ strokes[index].count) * 16777619u;
            for (unsigned point = 0; point < strokes[index].count; ++point) {
                const auto& position = points[strokes[index].start + point];
                hash = (hash ^ position.x) * 16777619u;
                hash = (hash ^ position.y) * 16777619u;
            }
        }
        snapshot.diagnostics = {{"completed_strokes", completed_strokes}, {"point_count", point_count},
            {"current_points", contact == Contact::canvas ? strokes[completed_strokes].count : 0},
            {"active_contact", state.contact_down}, {"storage_limited", limited}, {"stroke_hash", hash}};
        return snapshot;
    }

    ExerciseEvent touch(uint16_t x, uint16_t y, bool down) override {
        if (down) {
            if (!state.contact_down) {
                state.contact_down = true;
                contact = Contact::ignored;
                if (in_continue(x, y)) contact = Contact::continuation;
                else if (in_canvas(x, y)) {
                    if (completed_strokes == max_strokes || point_count == max_points) limited = true;
                    else {
                        contact = Contact::canvas;
                        strokes[completed_strokes] = {point_count, 0};
                        state.phase = "drawing";
                    }
                }
            } else if (contact == Contact::continuation && !in_continue(x, y)) contact = Contact::ignored;
            const bool changed = contact == Contact::canvas && append(x, y);
            return {true, changed, false, contact == Contact::continuation ? 1u : 0u, 0};
        }
        if (!state.contact_down) return {};
        state.contact_down = false;
        const auto released = contact;
        contact = Contact::none;
        if (released == Contact::canvas) {
            ++completed_strokes;
            state.completed = completed_strokes >= 2;
            state.can_continue = state.completed;
            state.phase = state.completed ? "ready" : "released";
            return {true, true, false, 0, 0};
        }
        if (released == Contact::continuation && state.can_continue) {
            state.can_continue = false;
            state.phase = "resuming";
            return {true, false, true, 1, 0};
        }
        return {false, false, false, released == Contact::continuation ? 1u : 0u, 0};
    }

    void render(Surface& surface) const override {
        surface.pixels.fill(0xff172335u);
        surface.text(88, 4, "FREEHAND TEST", 0xffedf4ffu);
        surface.text(80, 16, "STROKES " + std::to_string(completed_strokes), 0xffb8c6dcu);
        surface.rectangle(23, 31, 233, 137, 0xff93a8c5u);
        surface.rectangle(24, 32, 232, 136, 0xffedf4ffu);
        if (!point_count) surface.text(80, 76, "DRAW TWO STROKES", 0xff47566bu);
        const unsigned stored = completed_strokes + (contact == Contact::canvas ? 1 : 0);
        for (unsigned index = 0; index < stored; ++index) {
            const auto& stroke = strokes[index];
            for (unsigned point = 0; point < stroke.count; ++point) {
                const auto& position = points[stroke.start + point];
                const auto& previous = points[stroke.start + (point ? point - 1 : 0)];
                surface.line(previous.x, previous.y, position.x, position.y, ink);
            }
        }
        surface.rectangle(72, 148, 184, 184, state.can_continue ? 0xff42d39fu : 0xff47566bu);
        surface.rectangle(73, 149, 183, 183, 0xff24354cu);
        surface.text(80, 160, "CONTINUE", state.can_continue ? 0xffedf4ffu : 0xff78879bu, 2);
    }
};
}
