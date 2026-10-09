#pragma once

#include "bc_quiz.h"

namespace brainage_custom {
inline const ExerciseDescriptor& launch_exercise() {
    static const ExerciseDescriptor descriptor{"arithmetic-2plus2", []() -> std::unique_ptr<Exercise> {
        return std::make_unique<ArithmeticQuiz>();
    }};
    return descriptor;
}
}
