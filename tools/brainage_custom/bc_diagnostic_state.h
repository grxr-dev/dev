#pragma once

#include <string>

namespace brainage_custom::diagnostics {
struct ControlOrder {
    std::string session;
    unsigned sequence = 0;
    const char* consume(const std::string& token, unsigned number) {
        if (token != session) return "session_mismatch";
        if (!number || number != sequence + 1) return "stale_or_out_of_order";
        sequence = number;
        return nullptr;
    }
};

struct Session {
    ControlOrder control{};
    std::string last_input{};
    const char* input_source = "none";
    const char* input_action = "none";
    const char* rejection = "";
    unsigned input_sequence = 0;
    unsigned input_answer = 0;
    unsigned touch_x = 0, touch_y = 0, touch_target = 0;
    bool touch_down = false;
    uint64_t touch_events = 0;
    uint64_t delivery_before = 0;
    bool consumed = false;
    const char* capture_name = "";
    void* window = nullptr;
};
}
