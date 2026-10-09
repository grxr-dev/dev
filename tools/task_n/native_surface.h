#pragma once

#include <array>
#include <cstdint>
#include <string>
#include "mini_exercise_state.h"

namespace brainage_native {
struct NativeSurface {
    static constexpr unsigned width = 256, height = 192;
    std::array<uint32_t, width * height> pixels{};

    static std::array<uint8_t, 7> glyph(char character) {
        switch (character) {
            case 'A': return {14,17,17,31,17,17,17};
            case 'B': return {30,17,17,30,17,17,30};
            case 'C': return {14,17,16,16,16,17,14};
            case 'D': return {30,17,17,17,17,17,30};
            case 'E': return {31,16,16,30,16,16,31};
            case 'G': return {14,17,16,23,17,17,15};
            case 'H': return {17,17,17,31,17,17,17};
            case 'I': return {31,4,4,4,4,4,31};
            case 'M': return {17,27,21,21,17,17,17};
            case 'N': return {17,25,25,21,19,19,17};
            case 'O': return {14,17,17,17,17,17,14};
            case 'P': return {30,17,17,30,16,16,16};
            case 'R': return {30,17,17,30,20,18,17};
            case 'S': return {15,16,16,14,1,1,30};
            case 'T': return {31,4,4,4,4,4,4};
            case 'U': return {17,17,17,17,17,17,14};
            case 'V': return {17,17,17,17,17,10,4};
            case 'X': return {17,17,10,4,10,17,17};
            case '0': return {14,17,19,21,25,17,14};
            case '1': return {4,12,4,4,4,4,14};
            case '2': return {14,17,1,2,4,8,31};
            case '3': return {30,1,1,14,1,1,30};
            case '4': return {2,6,10,18,31,2,2};
            case '5': return {31,16,16,30,1,1,30};
            case '+': return {0,4,4,31,4,4,0};
            case '=': return {0,0,31,0,31,0,0};
            case '?': return {14,17,1,2,4,0,4};
            default: return {};
        }
    }

    void rectangle(unsigned left, unsigned top, unsigned right, unsigned bottom, uint32_t color) {
        for (unsigned y = top; y <= bottom && y < height; ++y)
            for (unsigned x = left; x <= right && x < width; ++x) pixels[y * width + x] = color;
    }

    void text(unsigned x, unsigned y, const std::string& value, uint32_t color, unsigned scale = 1) {
        for (char character : value) {
            const auto rows = glyph(character);
            for (unsigned row = 0; row < 7; ++row)
                for (unsigned column = 0; column < 5; ++column)
                    if (rows[row] & (1u << (4 - column)))
                        rectangle(x + column * scale, y + row * scale,
                            x + (column + 1) * scale - 1, y + (row + 1) * scale - 1, color);
            x += 6 * scale;
        }
    }

    void paint(const MiniExercise& exercise) {
        pixels.fill(0xff172335u);
        text(20, 14, "BRAIN AGE NATIVE EXERCISE", 0xffedf4ffu);
        text(74, 36, "2 + 2 = ?", 0xffedf4ffu, 2);
        const uint32_t result = exercise.completed ? 0xff42d39fu : 0xffff8795u;
        text(78, 62, exercise.completed ? "CORRECT" : exercise.answers.empty() ? "CHOOSE" : "INCORRECT",
            exercise.answers.empty() ? 0xffedf4ffu : result);
        text(86, 78, "ATTEMPTS " + std::to_string(exercise.answers.size()), 0xffb8c6dcu);
        for (unsigned index = 0; index < 3; ++index) {
            const unsigned left = 24 + index * 74;
            rectangle(left, 96, left + 60, 136, 0xff93a8c5u);
            rectangle(left + 1, 97, left + 59, 135, 0xff30445eu);
            text(left + 23, 106, std::to_string(index + 3), exercise.completed ? 0xff78879bu : 0xffedf4ffu, 3);
        }
        rectangle(72, 148, 184, 184, exercise.continue_available() ? 0xff42d39fu : 0xff47566bu);
        rectangle(73, 149, 183, 183, 0xff24354cu);
        text(80, 160, "CONTINUE", exercise.continue_available() ? 0xffedf4ffu : 0xff78879bu, 2);
    }
};
}
