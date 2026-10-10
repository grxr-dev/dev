#pragma once
#include "bc_decuma_adapter.h"
#include <string>
#include <array>
namespace brainage_custom {
// success describes operation completion, independent of candidate availability.
// candidate is meaningful only when candidate_available; metric is diagnostic.
// Legacy scalar = first group-1 code, NOT the complete original numeric answer.
// Ordered output characters, not ranked alternative answers. Group 0 is a
// per-call append delta; group 1 replaces the current suffix. Counts are raw
// recognizer segment counts; code_count measures the bounded terminated codes.
struct DigitOutputGroup {
    uint32_t returned_count = 0, code_count = 0;
    std::array<uint16_t,16> codes{};
    // First code from the original worker's 020A3FFC accessor per position.
    // A secondary representation used by title policy; no rank is claimed.
    std::array<uint16_t,16> accessor_codes{};
};
struct DigitResult {
    bool success = false;
    bool candidate_available = false;
    uint16_t candidate = 0;
    uint32_t metric = 0, error = 0;
    uint64_t wall_us = 0, instructions = 0;
    std::string message;
    std::array<DigitOutputGroup,2> groups{};
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
