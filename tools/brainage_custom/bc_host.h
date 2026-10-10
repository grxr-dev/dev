#pragma once

#include <array>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif
#include "state.h"
#include "io.h"
#include "scheduler.h"
#include "sha1.h"
#include "gpu2d.h"
#include "vram.h"
#include "frontend.h"
#include "debug_server.h"
#include "bc_activation.h"
#include "bc_catalog.h"
#include "bc_private_digit_recognizer.h"
#include "bc_diagnostic_state.h"

namespace brainage_custom {
inline bool identity_ok = false;
inline bool enabled = false;
inline bool ds_presentation = false;
inline bool used = false;
inline void compiled_instruction();

inline uint32_t peek_word(uint32_t address) {
    uint32_t value = 0;
    for (unsigned index = 0; index < 4; ++index)
        value |= uint32_t(bus_debug_read8(9, address + index)) << (index * 8);
    return value;
}

inline std::string flash_digest() {
    const uint8_t* bytes = nullptr;
    uint32_t size = 0;
    bool dirty = false;
    if (!nds_io_cartridge_save_snapshot(&bytes, &size, &dirty) || size != 262144)
        throw std::runtime_error("Brain Age custom host requires 256 KiB Flash");
    return gba::sha1(bytes, size).hex();
}

inline uint64_t frontend_hold_presents() {
#if defined(NDS_NATIVE_HOLD_FRONTEND_SERVICE)
    return nds_frontend_native_present_count();
#else
    return 0;
#endif
}

struct Hold {
    const uint32_t* registers;
    std::array<uint32_t, 16> saved{};
    uint32_t cpsr;
    uint64_t cycles, cycles7, instruction9, instruction7;
    std::string flash;
    bool continued = false;
    const char* backend = "tier3";
    const char* exercise_id = "";
    std::unique_ptr<Exercise> exercise{};
    std::unique_ptr<Surface> surface{};
    ExerciseStatus final_status{};
    unsigned begin_count = 0, render_count = 0, touch_count = 0, status_queries = 0;
    diagnostics::Session audit{};
};

inline ExerciseStatus exercise_status(const Hold& hold) {
    return hold.exercise ? hold.exercise->status() : hold.final_status;
}

inline void dispatch_action(Hold& hold, const char* action, unsigned value);
}

#include "bc_diagnostics.h"

namespace brainage_custom {
inline void initialize(const char* rom_sha1, const uint8_t* rom_bytes = nullptr, size_t rom_size = 0) {
    active_rom.bind(rom_sha1, rom_bytes, rom_size);
    identity_ok = rom_sha1 && std::strcmp(rom_sha1, "b8a105bacc3234dede8d4465df0869f2b922a0e2") == 0;
    const auto configuration = activation_from_environment();
    if (configuration.enabled && !identity_ok)
        throw std::runtime_error("Brain Age custom host requires the exact ROM SHA-1");
    enabled = configuration.enabled && identity_ok;
    ds_presentation = enabled && configuration.presentation;
    diagnostics::initialize();
    if (identity_ok && (enabled || diagnostics::observing()))
        nds_set_compiled_instruction_hook(compiled_instruction);
}

inline void render_exercise(Hold& hold) {
    hold.exercise->render(*hold.surface);
    ++hold.render_count;
    diagnostics::record("exercise_render", hold);
    diagnostics::refresh_panel(hold);
}

inline void apply_result(Hold& hold, const ExerciseStatus& before, const ExerciseEvent& result) {
    const auto after = hold.exercise->status();
    ++hold.status_queries;
    diagnostics::record("host_can_continue", hold);
    if (result.changed) render_exercise(hold);
    if (result.selected) {
        hold.audit.input_answer = result.selected;
        diagnostics::record("choose", hold);
        diagnostics::record(after.completed ? "correct_result" : "incorrect_result", hold);
    }
    if (result.request_exit) {
        if ((!before.can_continue && !after.can_continue) || !after.completed || after.contact_down || hold.continued)
            throw std::runtime_error("custom exercise requested an unsafe or duplicate exit");
        hold.continued = true;
        diagnostics::record("continue", hold);
    }
}

inline void dispatch_action(Hold& hold, const char* action, unsigned value) {
    hold.audit.input_action = action;
    hold.audit.input_answer = value;
    hold.audit.rejection = "";
    const auto before = hold.exercise->status();
    ++hold.status_queries;
    const auto result = hold.exercise->diagnostic_action(action, value);
    if (result.accepted) apply_result(hold, before, result);
    else {
        hold.audit.rejection = "invalid_action_or_phase";
        diagnostics::record("control_rejected", hold);
    }
}

inline bool consume_touch(void* context, uint16_t x, uint16_t y, bool down) {
    auto& hold = *static_cast<Hold*>(context);
    hold.audit.input_source = "ds_touch";
    hold.audit.input_action = "touch";
    hold.audit.input_answer = 0;
    hold.audit.rejection = "";
    hold.audit.touch_x = x;
    hold.audit.touch_y = y;
    hold.audit.touch_down = down;
    hold.audit.delivery_before = nds_touch_observation().guest_deliveries;
    hold.audit.consumed = true;
    ++hold.audit.touch_events;
    const auto before = hold.exercise->status();
    ++hold.status_queries;
    const auto result = hold.exercise->touch(x, y, down);
    ++hold.touch_count;
    hold.audit.touch_target = result.target;
    diagnostics::record("exercise_touch", hold);
    diagnostics::record("touch_consumed", hold);
    apply_result(hold, before, result);
    if (!down && result.target && !result.accepted) {
        hold.audit.rejection = "invalid_action_or_phase";
        diagnostics::record("control_rejected", hold);
    }
    return true;
}

inline void run_exercise(Hold& hold) {
    const auto initial = nds_touch_observation();
    if (initial.down || initial.adc_x != 0 || initial.adc_y != 4095 || initial.owned || nds_gpu2d_bottom_presentation_owned())
        throw std::runtime_error("Brain Age custom host requires clean input and presentation");
    const auto& descriptor = launch_exercise();
    hold.exercise_id = descriptor.id;
    diagnostics::record("host_entered", hold);
    diagnostics::service_isolation_begin();
    digit_detail::PrivateDigitRecognizer recognizer;
    ExerciseServices services{&recognizer};
    struct ExerciseScope { Hold& hold; ~ExerciseScope(){hold.exercise.reset();} } exercise_scope{hold};
    hold.exercise = descriptor.create(services);
    if (!hold.exercise) throw std::runtime_error("custom exercise factory returned no instance");
    diagnostics::record("exercise_instantiated", hold);
    hold.exercise->begin();
    ++hold.begin_count;
    diagnostics::record("exercise_begin", hold);
    hold.surface = std::make_unique<Surface>();
    render_exercise(hold);
    struct OwnerScope {
        Hold& hold;
        ~OwnerScope() {
            nds_set_touch_owner(nullptr, nullptr);
            nds_gpu2d_set_bottom_presentation(nullptr);
            diagnostics::destroy_panel(hold);
        }
    } owners{hold};
    if (ds_presentation) nds_gpu2d_set_bottom_presentation(hold.surface->pixels.data());
    nds_set_touch_owner(consume_touch, &hold);
    if (!ds_presentation) diagnostics::create_panel(hold);
    diagnostics::record("panel_active", hold);
    while (!hold.continued) {
        if (ds_presentation) {
#if defined(NDS_NATIVE_HOLD_FRONTEND_SERVICE)
            if (!nds_frontend_service_native_hold())
                throw std::runtime_error("Brain Age custom host cancelled by frontend");
#endif
        } else diagnostics::service_panel(hold);
        diagnostics::poll(hold);
        if (!hold.continued) std::this_thread::sleep_for(std::chrono::milliseconds(20));
    }
    const auto final = nds_touch_observation();
    if (hold.exercise->status().contact_down || final.down || final.adc_x != 0 || final.adc_y != 4095 || final.guest_deliveries != initial.guest_deliveries)
        throw std::runtime_error("Brain Age custom input contact leaked");
    diagnostics::record("touch_release_clean", hold);
    nds_set_touch_owner(nullptr, nullptr);
    diagnostics::record("touch_owner_released", hold);
    nds_gpu2d_set_bottom_presentation(nullptr);
    diagnostics::destroy_panel(hold);
    hold.surface.reset();
    diagnostics::record("presentation_owner_released", hold);
    hold.final_status = hold.exercise->status();
    diagnostics::record("exercise_end", hold);
    hold.exercise.reset();
    diagnostics::record("exercise_destroyed", hold);
    const auto service_cleanup = recognizer.end_session();
    if (recognizer.active() || !service_cleanup.success) throw std::runtime_error("custom service cleanup failed");
    diagnostics::record_service_cleanup(service_cleanup);
    diagnostics::capture_presented(hold, "handoff");
    diagnostics::record("host_cleanup", hold);
}

inline void before_instruction(uint32_t pc, bool thumb, uint32_t raw, const uint32_t* registers, uint32_t cpsr, const char* backend = "tier3") {
    if ((!enabled && !diagnostics::observing()) || !identity_ok || used || g_nds_active != NDS_ARM9 || thumb || pc != 0x0204d790u) return;
    if (registers[0] != 0x41u || peek_word(0x020da3f0u) != 0x11u) return;
    Hold hold{registers, {}, cpsr, g_runtime_cycles, scheduler_cpu_cycles(1), g_insn_count[0], g_insn_count[1], flash_digest()};
    hold.backend = backend;
    std::memcpy(hold.saved.data(), registers, sizeof(uint32_t) * 16);
    diagnostics::record("boundary_context", hold);
    if (raw != 0xe92d4030u || registers[14] != 0x02050268u || peek_word(0x020da464u) != 0x32u || peek_word(0x020da3ecu) != 0x41u || peek_word(0x020da420u) != 1u) {
        diagnostics::record("gate_rejected", hold);
        return;
    }
    used = true;
    diagnostics::begin_session(hold);
    diagnostics::record(enabled ? "intercept" : "boundary_disabled", hold);
    if (!enabled) return;
    run_exercise(hold);
    if (std::memcmp(hold.saved.data(), registers, sizeof(uint32_t) * 16) != 0 ||
        g_runtime_cycles != hold.cycles || scheduler_cpu_cycles(1) != hold.cycles7 ||
        g_insn_count[0] != hold.instruction9 || g_insn_count[1] != hold.instruction7 ||
        flash_digest() != hold.flash || peek_word(0x020da464u) != 0x32u ||
        peek_word(0x020da3ecu) != 0x41u || peek_word(0x020da3f0u) != 0x11u || g_nds_terminal)
        throw std::runtime_error("Brain Age guest context changed during custom exercise");
    diagnostics::record("continue_original", hold);
}

inline void observe_entry(uint32_t pc, bool thumb, const uint32_t* registers, const char* backend) {
    diagnostics::observe_entry(pc, thumb, registers, backend);
}

inline void compiled_instruction() {
    const uint32_t pc = g_cpu.R[15];
    const bool thumb = (g_cpu.cpsr & 0x20u) != 0;
    observe_entry(pc, thumb, g_cpu.R, "compiled");
    if (g_nds_active == NDS_ARM9 && !thumb && pc == 0x0204d790u)
        before_instruction(pc, thumb, peek_word(pc), g_cpu.R, g_cpu.cpsr, "compiled");
}
}
