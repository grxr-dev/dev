#include "mini_exercise_state.h"
#include <cassert>
#include <cstdio>

int main() {
    brainage_native::MiniExercise exercise;
    assert(!exercise.resume() && exercise.answers.empty());
    assert(!exercise.choose(7) && exercise.answers.empty());
    assert(exercise.choose(3) && exercise.answers == std::vector<unsigned>{3});
    assert(exercise.phase == brainage_native::Phase::Incorrect && !exercise.completed);
    assert(!exercise.resume());
    assert(exercise.choose(5) && (exercise.answers == std::vector<unsigned>{3, 5}));
    assert(!exercise.completed && !exercise.resume());
    assert(exercise.choose(4) && (exercise.answers == std::vector<unsigned>{3, 5, 4}));
    assert(exercise.completed && exercise.continue_available());
    assert(!exercise.choose(4) && exercise.answers.size() == 3);
    assert(exercise.resume() && !exercise.resume());
    brainage_native::ControlOrder order{"fresh-session", 0};
    assert(order.consume("old-session", 1) && order.sequence == 0);
    assert(order.consume("fresh-session", 0) && order.sequence == 0);
    assert(order.consume("fresh-session", 2) && order.sequence == 0);
    assert(!order.consume("fresh-session", 1) && order.sequence == 1);
    assert(order.consume("fresh-session", 1) && order.sequence == 1);
    assert(!order.consume("fresh-session", 2) && order.sequence == 2);
    std::puts("PASS: wrong/correct phases, premature/duplicate Continue, invalid answer, stale session, sequence replay/order");
}
