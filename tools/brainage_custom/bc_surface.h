#pragma once

#include <array>
#include <cstdint>
#include <cstdlib>
#include <string>

namespace brainage_custom {
struct Surface {
    static constexpr unsigned width = 256, height = 192;
    std::array<uint32_t, width * height> pixels{};

    static std::array<uint8_t, 7> glyph(char character) {
        switch (character) {
            case 'A': return {14,17,17,31,17,17,17};
            case 'B': return {30,17,17,30,17,17,30};
            case 'C': return {14,17,16,16,16,17,14};
            case 'D': return {30,17,17,17,17,17,30};
            case 'E': return {31,16,16,30,16,16,31};
            case 'F': return {31,16,16,30,16,16,16};
            case 'G': return {14,17,16,23,17,17,15};
            case 'H': return {17,17,17,31,17,17,17};
            case 'I': return {31,4,4,4,4,4,31};
            case 'K': return {17,18,20,24,20,18,17};
            case 'L': return {16,16,16,16,16,16,31};
            case 'M': return {17,27,21,21,17,17,17};
            case 'N': return {17,25,25,21,19,19,17};
            case 'O': return {14,17,17,17,17,17,14};
            case 'P': return {30,17,17,30,16,16,16};
            case 'R': return {30,17,17,30,20,18,17};
            case 'S': return {15,16,16,14,1,1,30};
            case 'T': return {31,4,4,4,4,4,4};
            case 'U': return {17,17,17,17,17,17,14};
            case 'V': return {17,17,17,17,17,10,4};
            case 'W': return {17,17,17,21,21,21,10};
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

    void line(int start_x, int start_y, int end_x, int end_y, uint32_t color) {
        if (start_x < 0 || end_x < 0 || start_y < 0 || end_y < 0 ||
            start_x >= int(width) || end_x >= int(width) || start_y >= int(height) || end_y >= int(height)) return;
        const int delta_x = std::abs(end_x - start_x);
        const int delta_y = -std::abs(end_y - start_y);
        const int step_x = start_x < end_x ? 1 : -1;
        const int step_y = start_y < end_y ? 1 : -1;
        int error = delta_x + delta_y;
        while (true) {
            pixels[unsigned(start_y) * width + unsigned(start_x)] = color;
            if (start_x == end_x && start_y == end_y) break;
            const int doubled = 2 * error;
            if (doubled >= delta_y) { error += delta_y; start_x += step_x; }
            if (doubled <= delta_x) { error += delta_x; start_y += step_y; }
        }
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

};
}
