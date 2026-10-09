#pragma once

#include <cstring>
#include <cstdlib>

namespace brainage_custom {
struct Activation {
    bool enabled = false;
    bool presentation = false;
};

inline Activation activation(const char* stable, const char* legacy, const char* surface, const char* legacy_surface) {
    const char* selected = stable ? stable : legacy;
    const bool enabled = selected && std::strcmp(selected, "1") == 0;
    const char* presentation = surface ? surface : legacy_surface;
    return {enabled, enabled && (presentation ? std::strcmp(presentation, "1") == 0 : stable != nullptr)};
}

inline Activation activation_from_environment() {
    return activation(std::getenv("NDS_BRAINAGE_CUSTOM_EXERCISE"), std::getenv("NDS_TASK_J_CUSTOM_EXERCISE_PROBE"),
        std::getenv("NDS_BRAINAGE_NATIVE_PRESENTATION"), std::getenv("NDS_TASK_N_DS_PRESENTATION"));
}
}
