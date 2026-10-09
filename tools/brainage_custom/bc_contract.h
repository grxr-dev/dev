#pragma once

#include <cstdint>
#include <memory>
#include <string>
#include <vector>
#include "bc_surface.h"

namespace brainage_custom {
struct DiagnosticMetric {
    std::string name;
    uint64_t value;
};

struct ExerciseStatus {
    std::string phase = "inactive";
    std::vector<unsigned> answers;
    bool completed = false;
    bool can_continue = false;
    bool contact_down = false;
    std::vector<DiagnosticMetric> diagnostics;
};

struct ExerciseEvent {
    bool accepted = false;
    bool changed = false;
    bool request_exit = false;
    unsigned target = 0;
    unsigned selected = 0;
};

class Exercise {
public:
    virtual ~Exercise() = default;
    virtual void begin() = 0;
    virtual void render(Surface& surface) const = 0;
    virtual ExerciseEvent touch(uint16_t x, uint16_t y, bool down) = 0;
    virtual ExerciseStatus status() const = 0;
    virtual ExerciseEvent diagnostic_action(const char*, unsigned) { return {}; }
};

struct ExerciseDescriptor {
    const char* id;
    std::unique_ptr<Exercise> (*create)();
};
}
