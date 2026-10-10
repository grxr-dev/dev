#pragma once
#include "bc_decuma_adapter.h"
#include <string>
namespace brainage_custom {
// success describes operation completion, independent of candidate availability.
// candidate is meaningful only when candidate_available; metric is diagnostic.
struct DigitResult {
    bool success = false;
    bool candidate_available = false;
    uint16_t candidate = 0;
    uint32_t metric = 0, error = 0;
    uint64_t wall_us = 0, instructions = 0;
    std::string message;
};
class DigitRecognizer {
public:
    virtual ~DigitRecognizer() = default;
    virtual DigitResult begin_session() = 0;
    virtual DigitResult recognize_stroke(const decuma::Stroke&) = 0;
    virtual DigitResult end_session() = 0;
    virtual bool active() const = 0;
};
struct ExerciseServices { DigitRecognizer* digit_recognizer = nullptr; };
}
