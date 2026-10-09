#pragma once

#include <string>
#include <vector>

namespace brainage_native {
enum class Phase { Question, Incorrect, Completed, Resuming };

struct MiniExercise {
    Phase phase = Phase::Question;
    std::vector<unsigned> answers;
    bool completed = false;

    const char* phase_name() const {
        switch (phase) {
        case Phase::Question: return "question";
        case Phase::Incorrect: return "incorrect";
        case Phase::Completed: return "completed";
        case Phase::Resuming: return "resuming";
        }
        return "invalid";
    }

    bool choose(unsigned answer) {
        if (completed || (answer != 3 && answer != 4 && answer != 5)) return false;
        answers.push_back(answer);
        completed = answer == 4;
        phase = completed ? Phase::Completed : Phase::Incorrect;
        return true;
    }

    bool continue_available() const { return phase == Phase::Completed; }

    bool resume() {
        if (!continue_available()) return false;
        phase = Phase::Resuming;
        return true;
    }
};

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
}
