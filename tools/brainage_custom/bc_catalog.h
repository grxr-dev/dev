#pragma once

#include "bc_quiz.h"
#include "bc_freehand.h"
#include "bc_digit_probe.h"
#include "bc_digit_entry.h"
#include <cstdlib>
#include <cstring>
#include <stdexcept>

namespace brainage_custom {
inline const ExerciseDescriptor& exercise_descriptor(const char* id) {
    static const ExerciseDescriptor descriptors[] = {
        {"arithmetic-2plus2", [](ExerciseServices&) -> std::unique_ptr<Exercise> { return std::make_unique<ArithmeticQuiz>(); }},
        {"freehand-canvas", [](ExerciseServices&) -> std::unique_ptr<Exercise> { return std::make_unique<FreehandCanvas>(); }},
        {"digit-recognition-probe", [](ExerciseServices& services) -> std::unique_ptr<Exercise> { return std::make_unique<DigitProbe>(services); }},
        {"digit-entry-probe", [](ExerciseServices& services) -> std::unique_ptr<Exercise> { return std::make_unique<DigitEntryProbe>(services); }}
    };
    if (!id || !*id) return descriptors[0];
    for (const auto& descriptor : descriptors)
        if (std::strcmp(descriptor.id, id) == 0) return descriptor;
    throw std::runtime_error(std::string("unknown Brain Age custom exercise ID: ") + id);
}

inline const ExerciseDescriptor& launch_exercise() {
    return exercise_descriptor(std::getenv("NDS_BRAINAGE_CUSTOM_EXERCISE_ID"));
}
}
