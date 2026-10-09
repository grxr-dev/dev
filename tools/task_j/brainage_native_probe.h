#pragma once

#include <array>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <thread>
#include <stdexcept>
#include <string>
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
#include "mini_exercise_state.h"
#include "touch_state.h"
#include "native_surface.h"
#include "gpu2d.h"
#include "vram.h"
#include "debug_server.h"

namespace brainage_task_j {
inline bool identity_ok = false;
inline bool enabled = false;
inline bool used = false;
inline bool ds_presentation = false;
inline FILE* trace = nullptr;
inline unsigned sequence = 0;
inline void compiled_instruction();

inline void initialize(const char* rom_sha1) {
    identity_ok = rom_sha1 && std::strcmp(rom_sha1, "b8a105bacc3234dede8d4465df0869f2b922a0e2") == 0;
    const char* activation = std::getenv("NDS_TASK_J_CUSTOM_EXERCISE_PROBE");
    enabled = identity_ok && activation && std::strcmp(activation, "1") == 0;
    const char* presentation = std::getenv("NDS_TASK_N_DS_PRESENTATION");
    ds_presentation = enabled && presentation && std::strcmp(presentation, "1") == 0;
    const char* path = std::getenv("NDS_TASK_J_TRACE");
    if (path && *path) {
        trace = std::fopen(path, "wb");
        if (!trace) throw std::runtime_error("Task J trace cannot be opened");
    }
    if (activation && std::strcmp(activation, "1") == 0 && !identity_ok)
        throw std::runtime_error("Task J requires the exact Brain Age ROM SHA-1");
    const char* observer = std::getenv("NDS_TASK_K_TRACE");
    if (identity_ok && (enabled || trace || (observer && *observer)))
        nds_set_compiled_instruction_hook(compiled_instruction);
}

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
        throw std::runtime_error("Task J requires 256 KiB Flash");
    return gba::sha1(bytes, size).hex();
}

struct Hold {
    const uint32_t* registers;
    std::array<uint32_t, 16> saved;
    uint32_t cpsr;
    uint64_t cycles;
    uint64_t cycles7;
    uint64_t instruction9;
    uint64_t instruction7;
    std::string flash;
    bool continued = false;
    const char* backend = "tier3";
    brainage_native::MiniExercise exercise{};
    brainage_native::ControlOrder control{};
    std::string last_input{};
    const char* input_source = "none";
    const char* input_action = "none";
    const char* rejection = "";
    unsigned input_sequence = 0;
    unsigned input_answer = 0;
    brainage_native::TouchContact contact{};
    unsigned touch_x = 0, touch_y = 0, touch_target = 0;
    bool touch_down = false;
    uint64_t touch_events = 0;
    uint64_t delivery_before = 0;
    bool consumed = false;
    std::unique_ptr<brainage_native::NativeSurface> surface{};
    const char* capture_name = "";
};

inline std::string pixel_digest(const uint32_t* pixels) {
    std::vector<uint8_t> rgb;
    rgb.reserve(256 * 192 * 3);
    for (unsigned index = 0; index < 256 * 192; ++index) {
        rgb.push_back(uint8_t(pixels[index] >> 16));
        rgb.push_back(uint8_t(pixels[index] >> 8));
        rgb.push_back(uint8_t(pixels[index]));
    }
    return gba::sha1(rgb.data(), rgb.size()).hex();
}

inline std::string video_digest() {
    std::vector<uint8_t> bytes;
    for (const char* region : {"vramA", "vramB", "vramC", "vramD", "vramE", "vramF", "vramG", "vramH", "vramI", "palA", "palB", "oam"}) {
        const uint8_t* data = nullptr;
        uint32_t size = 0;
        if (!nds_video_get_region(region, &data, &size)) throw std::runtime_error("Task N graphics region missing");
        bytes.insert(bytes.end(), data, data + size);
    }
    return gba::sha1(bytes.data(), bytes.size()).hex();
}

inline void record(const char* event, const Hold& hold) {
    if (!trace) return;
    std::fprintf(trace, "{\"sequence\":%u,\"event\":\"%s\",\"enabled\":%s,\"pc\":%u,\"current\":%u,\"requested\":%u,\"selected\":%u,\"cpu_cycles\":%llu,\"system_cycles\":%llu,\"cycles7\":%llu,\"insn9\":%llu,\"insn7\":%llu,\"cpsr\":%u,\"terminal\":%s,\"flash_sha1\":\"%s\",\"r\":[",
        ++sequence, event, enabled ? "true" : "false", 0x0204d790u,
        peek_word(0x020da464u), peek_word(0x020da3ecu), peek_word(0x020da3f0u),
        (unsigned long long)g_runtime_cycles, (unsigned long long)(g_runtime_cycles >> 1),
        (unsigned long long)scheduler_cpu_cycles(1),
        (unsigned long long)g_insn_count[0], (unsigned long long)g_insn_count[1],
        hold.cpsr, g_nds_terminal ? "true" : "false", flash_digest().c_str());
    for (unsigned index = 0; index < 16; ++index)
        std::fprintf(trace, "%s%u", index ? "," : "", hold.registers[index]);
    std::fprintf(trace, "],\"backend\":\"%s\",\"forced_tier3\":%s,\"session\":\"%s\",\"phase\":\"%s\",\"attempts\":%u,\"completed\":%s,\"continue_available\":%s,\"control_sequence\":%u,\"action_sequence\":%u,\"source\":\"%s\",\"action\":\"%s\",\"answer\":%u,\"rejection\":\"%s\",\"answers\":[",
        hold.backend, g_nds_force_tier3 ? "true" : "false", hold.control.session.c_str(),
        hold.exercise.phase_name(), unsigned(hold.exercise.answers.size()), hold.exercise.completed ? "true" : "false",
        hold.exercise.continue_available() ? "true" : "false", hold.control.sequence, hold.input_sequence,
        hold.input_source, hold.input_action, hold.input_answer, hold.rejection);
    for (unsigned index = 0; index < hold.exercise.answers.size(); ++index)
        std::fprintf(trace, "%s%u", index ? "," : "", hold.exercise.answers[index]);
    const auto touch = nds_touch_observation();
    std::fprintf(trace, "],\"touch_x\":%u,\"touch_y\":%u,\"touch_down\":%s,\"touch_target\":%u,\"touch_events\":%llu,\"consumed\":%s,\"touch_owner\":%s,\"native_contact\":%s,\"guest_pen_down\":%s,\"guest_adc_x\":%u,\"guest_adc_y\":%u,\"guest_touch_deliveries\":%llu,\"event_guest_deliveries\":%llu",
        hold.touch_x, hold.touch_y, hold.touch_down ? "true" : "false", hold.touch_target,
        (unsigned long long)hold.touch_events, hold.consumed ? "true" : "false", touch.owned ? "true" : "false",
        hold.contact.down ? "true" : "false", touch.down ? "true" : "false", touch.adc_x, touch.adc_y,
        (unsigned long long)touch.guest_deliveries,
        (unsigned long long)(touch.guest_deliveries - hold.delivery_before));
    if (ds_presentation) {
        uint16_t width = 256;
        const auto* bottom = nds_gpu2d_presented_framebuffer(1, &width, false);
        std::fprintf(trace, ",\"presentation_owner\":%s,\"bottom_source\":\"%s\",\"top_source\":\"guest\",\"surface_width\":%u,\"surface_height\":192,\"native_sha1\":\"%s\",\"presented_bottom_sha1\":\"%s\",\"guest_top_sha1\":\"%s\",\"guest_bottom_sha1\":\"%s\",\"video_sha1\":\"%s\",\"capture\":\"%s\",\"popup\":false",
            nds_gpu2d_bottom_presentation_owned() ? "true" : "false", nds_gpu2d_bottom_presentation_owned() ? "native" : "guest", width,
            hold.surface ? pixel_digest(hold.surface->pixels.data()).c_str() : "", pixel_digest(bottom).c_str(),
            pixel_digest(nds_gpu2d_framebuffer(0)).c_str(), pixel_digest(nds_gpu2d_framebuffer(1)).c_str(), video_digest().c_str(), hold.capture_name);
    }
    std::fputs("}\n", trace);
    std::fflush(trace);
}

inline void capture_presented(Hold& hold, const char* name) {
    const char* root = std::getenv("NDS_TASK_N_CAPTURE_ROOT");
    if (!root || !*root) throw std::runtime_error("Task N requires an isolated capture root");
    for (unsigned screen = 0; screen < 2; ++screen) {
        const std::string path = std::string(root) + "/surface-" + name + (screen ? "-B.json" : "-A.json");
        if (FILE* previous = std::fopen(path.c_str(), "rb")) {
            std::fclose(previous);
            throw std::runtime_error("Task N will not overwrite a capture");
        }
        const std::string response = debug_framebuffer_response(screen);
        FILE* output = std::fopen(path.c_str(), "wb");
        if (!output) throw std::runtime_error("Task N readback capture cannot be written");
        const bool written = std::fwrite(response.data(), 1, response.size(), output) == response.size();
        std::fclose(output);
        if (!written) throw std::runtime_error("Task N readback capture write failed");
    }
    hold.capture_name = name;
    record("capture_complete", hold);
    hold.capture_name = "";
}

#if defined(_WIN32)
inline void paint_panel(HWND window, HDC dc) {
    RECT bounds{};
    GetClientRect(window, &bounds);
    HBRUSH background = CreateSolidBrush(RGB(23, 35, 53));
    FillRect(dc, &bounds, background);
    DeleteObject(background);
    SetBkMode(dc, TRANSPARENT);
    SetTextColor(dc, RGB(245, 248, 255));
    HFONT font = CreateFontW(24, 0, 0, 0, FW_SEMIBOLD, FALSE, FALSE, FALSE,
        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY,
        DEFAULT_PITCH, L"Segoe UI");
    HGDIOBJ previous = SelectObject(dc, font);
    const auto* hold = reinterpret_cast<const Hold*>(GetWindowLongPtrW(window, GWLP_USERDATA));
    std::wstring content = L"Brain Age Native Exercise Test\n\n2 + 2 = ?\n";
    if (hold) {
        if (hold->exercise.completed) SetTextColor(dc, RGB(110, 245, 170));
        else if (!hold->exercise.answers.empty()) SetTextColor(dc, RGB(255, 150, 150));
        content += hold->exercise.completed ? L"Correct! Mini-exercise complete." :
            hold->exercise.answers.empty() ? L"Choose an answer." : L"Incorrect. Try again.";
        content += L"\nAttempts: " + std::to_wstring(hold->exercise.answers.size()) + L"  Answers:";
        for (unsigned answer : hold->exercise.answers) content += L" " + std::to_wstring(answer);
    }
    RECT text{24, 18, bounds.right - 24, 172};
    DrawTextW(dc, content.c_str(), -1, &text, DT_LEFT | DT_WORDBREAK);
    SelectObject(dc, previous);
    DeleteObject(font);
}

inline void capture_panel(HWND window) {
    const char* path = std::getenv("NDS_TASK_J_PANEL_CAPTURE");
    if (!path || !*path) return;
    RECT bounds{};
    GetClientRect(window, &bounds);
    const int width = bounds.right;
    const int height = bounds.bottom;
    HDC source = GetDC(window);
    HDC canvas = CreateCompatibleDC(source);
    HBITMAP bitmap = CreateCompatibleBitmap(source, width, height);
    HGDIOBJ previous = SelectObject(canvas, bitmap);
    const bool printed = PrintWindow(window, canvas, PW_CLIENTONLY) != 0;
    SelectObject(canvas, previous);
    BITMAPINFO info{};
    info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    info.bmiHeader.biWidth = width;
    info.bmiHeader.biHeight = -height;
    info.bmiHeader.biPlanes = 1;
    info.bmiHeader.biBitCount = 32;
    info.bmiHeader.biCompression = BI_RGB;
    std::vector<uint8_t> pixels(size_t(width) * height * 4);
    const bool copied = GetDIBits(source, bitmap, 0, height, pixels.data(), &info, DIB_RGB_COLORS) == height;
    DeleteObject(bitmap);
    DeleteDC(canvas);
    ReleaseDC(window, source);
    if (!printed || !copied) throw std::runtime_error("Task J native panel capture failed");
    BITMAPFILEHEADER header{};
    header.bfType = 0x4d42;
    header.bfOffBits = sizeof(header) + sizeof(info.bmiHeader);
    header.bfSize = header.bfOffBits + DWORD(pixels.size());
    const std::string checkpoint_path = std::string(path) + "." + std::to_string(sequence) + ".bmp";
    FILE* output = std::fopen(checkpoint_path.c_str(), "wb");
    if (!output) throw std::runtime_error("Task J panel capture cannot be opened");
    std::fwrite(&header, sizeof(header), 1, output);
    std::fwrite(&info.bmiHeader, sizeof(info.bmiHeader), 1, output);
    std::fwrite(pixels.data(), pixels.size(), 1, output);
    std::fclose(output);
}

inline void refresh_panel(HWND window, const Hold& hold) {
    EnableWindow(GetDlgItem(window, 1), hold.exercise.continue_available());
    for (unsigned answer : {3u, 4u, 5u}) EnableWindow(GetDlgItem(window, answer), !hold.exercise.completed);
    RedrawWindow(window, nullptr, nullptr, RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN | RDW_UPDATENOW);
    capture_panel(window);
}

inline void apply_action(HWND window, Hold& hold, const char* action, unsigned answer) {
    hold.input_action = action;
    hold.input_answer = answer;
    hold.rejection = "";
    if (std::strcmp(action, "sample") == 0) {
        record("held_sample", hold);
    } else if (std::strcmp(action, "choose") == 0 && hold.exercise.choose(answer)) {
        if (hold.surface) hold.surface->paint(hold.exercise);
        record("choose", hold);
        record(hold.exercise.completed ? "correct_result" : "incorrect_result", hold);
        if (!hold.surface) refresh_panel(window, hold);
    } else if (std::strcmp(action, "continue") == 0 && !hold.contact.down && hold.exercise.resume()) {
        hold.continued = true;
        record("continue", hold);
    } else {
        hold.rejection = std::strcmp(action, "continue") == 0 ? "not_completed" : "invalid_action_or_phase";
        record("control_rejected", hold);
    }
}

inline bool route_touch(Hold& hold, HWND window, uint16_t x, uint16_t y, bool down) {
    hold.input_source = "ds_touch";
    hold.input_action = "touch";
    hold.input_answer = 0;
    hold.rejection = "";
    hold.touch_x = x;
    hold.touch_y = y;
    hold.touch_down = down;
    hold.touch_target = brainage_native::touch_target(x, y);
    hold.delivery_before = nds_touch_observation().guest_deliveries;
    hold.consumed = true;
    ++hold.touch_events;
    const unsigned released = hold.contact.receive(x, y, down);
    record("touch_consumed", hold);
    if (released == 1) apply_action(window, hold, "continue", 0);
    else if (released) apply_action(window, hold, "choose", released);
    return true;
}

inline bool consume_touch(void* context, uint16_t x, uint16_t y, bool down) {
    HWND window = reinterpret_cast<HWND>(context);
    auto& hold = *reinterpret_cast<Hold*>(GetWindowLongPtrW(window, GWLP_USERDATA));
    return route_touch(hold, window, x, y, down);
}

inline bool consume_surface_touch(void* context, uint16_t x, uint16_t y, bool down) {
    return route_touch(*static_cast<Hold*>(context), nullptr, x, y, down);
}

inline void poll_control(HWND window, Hold* hold) {
    const char* path = std::getenv("NDS_TASK_J_CONTROL");
    FILE* input = path && *path ? std::fopen(path, "rb") : nullptr;
    if (input) {
        char line[256]{};
        const bool read = std::fgets(line, sizeof(line), input) != nullptr;
        std::fclose(input);
        if (read && hold->last_input != line) {
            hold->last_input = line;
            char token[96]{}, command[16]{}, trailing[2]{};
            unsigned number = 0, answer = 0;
            const int fields = std::sscanf(line, "%95s %u %15s %u %1s", token, &number, command, &answer, trailing);
            unsigned x = 0, y = 0, down = 0;
            const int touch_fields = std::sscanf(line, "%95s %u %15s %u %u %u %1s", token, &number, command, &x, &y, &down, trailing);
            char checkpoint[16]{}, extra[2]{};
            const int capture_fields = std::sscanf(line, "%95s %u %15s %15s %1s", token, &number, command, checkpoint, extra);
            const bool capture = ds_presentation && std::strcmp(command, "capture") == 0;
            const bool capture_format = capture_fields == 4 && (std::strcmp(checkpoint, "initial") == 0 || std::strcmp(checkpoint, "incorrect") == 0 || std::strcmp(checkpoint, "correct") == 0);
            const bool raw_touch = std::strcmp(command, "touch") == 0;
            hold->input_source = "diagnostic";
            hold->input_sequence = number;
            hold->input_action = "invalid";
            hold->input_answer = answer;
            const bool known_action = std::strcmp(command, "choose") == 0 || std::strcmp(command, "sample") == 0 || std::strcmp(command, "continue") == 0;
            const bool format_ok = capture ? capture_format : raw_touch ? touch_fields == 6 && x <= 255 && y <= 191 && down <= 1 :
                known_action && (std::strcmp(command, "choose") == 0 ? fields == 4 : fields == 3);
            const char* rejected = format_ok ? hold->control.consume(token, number) : "invalid_format";
            if (rejected) {
                hold->rejection = rejected;
                record("control_rejected", *hold);
            } else if (capture) {
                hold->input_action = "capture";
                capture_presented(*hold, checkpoint);
            } else if (raw_touch) nds_set_touch(uint16_t(x), uint16_t(y), down != 0);
            else apply_action(window, *hold, command, answer);
        }
    }
}

inline LRESULT CALLBACK panel_proc(HWND window, UINT message, WPARAM parameter, LPARAM detail) {
    auto* hold = reinterpret_cast<Hold*>(GetWindowLongPtrW(window, GWLP_USERDATA));
    if (message == WM_PAINT) {
        PAINTSTRUCT paint{};
        HDC dc = BeginPaint(window, &paint);
        paint_panel(window, dc);
        EndPaint(window, &paint);
        return 0;
    }
    if (message == WM_PRINTCLIENT) {
        paint_panel(window, reinterpret_cast<HDC>(parameter));
        return 0;
    }
    if (message == WM_CLOSE) return 0;
    if (hold && message == WM_COMMAND && HIWORD(parameter) == BN_CLICKED) {
        hold->input_source = "native_ui";
        hold->input_sequence = 0;
        const unsigned control = LOWORD(parameter);
        if (control == 1) apply_action(window, *hold, "continue", 0);
        else if (control >= 3 && control <= 5) apply_action(window, *hold, "choose", control);
        return 0;
    }
    if (hold && message == WM_TIMER) {
        poll_control(window, hold);
        return 0;
    }
    return DefWindowProcW(window, message, parameter, detail);
}

inline void show_surface(Hold& hold) {
    const auto initial_touch = nds_touch_observation();
    if (initial_touch.down || initial_touch.adc_x != 0 || initial_touch.adc_y != 0xfff ||
        initial_touch.owned || nds_gpu2d_bottom_presentation_owned())
        throw std::runtime_error("Task N requires clean input and no presentation owner");
    hold.delivery_before = initial_touch.guest_deliveries;
    hold.surface = std::make_unique<brainage_native::NativeSurface>();
    hold.surface->paint(hold.exercise);
    nds_gpu2d_set_bottom_presentation(hold.surface->pixels.data());
    nds_set_touch_owner(consume_surface_touch, &hold);
    struct OwnerScope {
        ~OwnerScope() {
            nds_set_touch_owner(nullptr, nullptr);
            nds_gpu2d_set_bottom_presentation(nullptr);
        }
    } owner_scope;
    record("panel_active", hold);
    while (!hold.continued) {
        poll_control(nullptr, &hold);
        if (!hold.continued) std::this_thread::sleep_for(std::chrono::milliseconds(20));
    }
    const auto final_touch = nds_touch_observation();
    if (hold.contact.down || final_touch.down || final_touch.adc_x != 0 || final_touch.adc_y != 0xfff ||
        final_touch.guest_deliveries != initial_touch.guest_deliveries)
        throw std::runtime_error("Task N contact leaked");
    record("touch_release_clean", hold);
    nds_set_touch_owner(nullptr, nullptr);
    record("touch_owner_released", hold);
    nds_gpu2d_set_bottom_presentation(nullptr);
    hold.surface.reset();
    record("presentation_owner_released", hold);
    capture_presented(hold, "handoff");
}

inline void show_panel(Hold& hold) {
    WNDCLASSW panel{};
    panel.lpfnWndProc = panel_proc;
    panel.hInstance = GetModuleHandleW(nullptr);
    panel.hCursor = LoadCursorW(nullptr, MAKEINTRESOURCEW(32512));
    panel.lpszClassName = L"BrainAgeTaskJNativeProbe";
    if (!RegisterClassW(&panel) && GetLastError() != ERROR_CLASS_ALREADY_EXISTS)
        throw std::runtime_error("Task J panel class creation failed");
    HWND window = CreateWindowExW(0, panel.lpszClassName, L"Brain Age Native Exercise Test",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU, CW_USEDEFAULT, CW_USEDEFAULT, 518, 422,
        nullptr, nullptr, panel.hInstance, nullptr);
    if (!window) throw std::runtime_error("Task J native window creation failed");
    SetWindowLongPtrW(window, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(&hold));
    HWND button = CreateWindowExW(0, L"BUTTON", L"Continue to Calculations x20",
        WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON, 144, 296, 226, 74,
        window, reinterpret_cast<HMENU>(1), panel.hInstance, nullptr);
    if (!button) throw std::runtime_error("Task J Continue control creation failed");
    SendMessageW(button, WM_SETFONT, reinterpret_cast<WPARAM>(GetStockObject(DEFAULT_GUI_FONT)), TRUE);
    for (unsigned answer : {3u, 4u, 5u}) {
        const std::wstring label = std::to_wstring(answer);
        HWND choice = CreateWindowExW(0, L"BUTTON", label.c_str(), WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
            48 + int(answer - 3) * 148, 192, 122, 82, window, reinterpret_cast<HMENU>(uintptr_t(answer)), panel.hInstance, nullptr);
        if (!choice) throw std::runtime_error("Native answer control creation failed");
        SendMessageW(choice, WM_SETFONT, reinterpret_cast<WPARAM>(GetStockObject(DEFAULT_GUI_FONT)), TRUE);
    }
    EnableWindow(button, FALSE);
    ShowWindow(window, SW_SHOWNORMAL);
    UpdateWindow(window);
    if (!SetTimer(window, 1, 50, nullptr)) throw std::runtime_error("Task J input polling failed");
    const auto initial_touch = nds_touch_observation();
    if (initial_touch.down || initial_touch.adc_x != 0 || initial_touch.adc_y != 0xfff || initial_touch.owned)
        throw std::runtime_error("Native touch ownership requires clean guest contact");
    hold.delivery_before = initial_touch.guest_deliveries;
    nds_set_touch_owner(consume_touch, window);
    struct OwnerScope {
        ~OwnerScope() { nds_set_touch_owner(nullptr, nullptr); }
    } owner_scope;
    record("panel_active", hold);
    capture_panel(window);
    MSG message{};
    while (!hold.continued) {
        if (GetMessageW(&message, nullptr, 0, 0) <= 0)
            throw std::runtime_error("Task J panel interrupted without Continue");
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
    KillTimer(window, 1);
    const auto final_touch = nds_touch_observation();
    if (hold.contact.down || final_touch.down || final_touch.adc_x != 0 || final_touch.adc_y != 0xfff ||
        final_touch.guest_deliveries != initial_touch.guest_deliveries)
        throw std::runtime_error("Native touch leaked or contact remains active");
    record("touch_release_clean", hold);
    nds_set_touch_owner(nullptr, nullptr);
    record("touch_owner_released", hold);
    DestroyWindow(window);
}
#endif

inline void before_instruction(uint32_t pc, bool thumb, uint32_t raw, const uint32_t* registers, uint32_t cpsr, const char* backend = "tier3") {
    if ((!enabled && !trace) || !identity_ok || used || g_nds_active != NDS_ARM9 || thumb || pc != 0x0204d790u) return;
    if (registers[0] != 0x41u || peek_word(0x020da3f0u) != 0x11u) return;
    Hold hold{registers, {}, cpsr, g_runtime_cycles, scheduler_cpu_cycles(1),
        g_insn_count[0], g_insn_count[1], flash_digest()};
    hold.backend = backend;
    std::memcpy(hold.saved.data(), registers, sizeof(uint32_t) * 16);
    record("boundary_context", hold);
    if (raw != 0xe92d4030u || registers[14] != 0x02050268u ||
        peek_word(0x020da464u) != 0x32u || peek_word(0x020da3ecu) != 0x41u ||
        peek_word(0x020da420u) != 1u) {
        record("gate_rejected", hold);
        return;
    }
    used = true;
    if (enabled) {
        hold.control.session = std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());
#if defined(_WIN32)
        hold.control.session += "-" + std::to_string(GetCurrentProcessId());
#endif
    }
    record(enabled ? "intercept" : "boundary_disabled", hold);
    if (!enabled) return;
#if defined(_WIN32)
    if (ds_presentation) show_surface(hold);
    else show_panel(hold);
#else
    throw std::runtime_error("Task J native panel currently requires Windows");
#endif
    if (std::memcmp(hold.saved.data(), registers, sizeof(uint32_t) * 16) != 0 ||
        g_runtime_cycles != hold.cycles || scheduler_cpu_cycles(1) != hold.cycles7 ||
        g_insn_count[0] != hold.instruction9 || g_insn_count[1] != hold.instruction7 ||
        flash_digest() != hold.flash || peek_word(0x020da464u) != 0x32u ||
        peek_word(0x020da3ecu) != 0x41u || peek_word(0x020da3f0u) != 0x11u || g_nds_terminal)
        throw std::runtime_error("Task J guest context changed during native hold");
    record("continue_original", hold);
}

inline void observe_entry(uint32_t pc, bool thumb, const uint32_t* registers, const char* backend) {
    if (!identity_ok || g_nds_active != NDS_ARM9 || thumb) return;
    const char* kind = pc == 0x0204d790u ? "lifecycle" :
        pc == 0x020610b4u ? "rules_initializer" :
        pc == 0x02027a28u ? "calculation_constructor" :
        pc == 0x0200de78u ? "write_api" : nullptr;
    if (!kind) return;
    static FILE* output = [] {
        const char* path = std::getenv("NDS_TASK_K_TRACE");
        return path && *path ? std::fopen(path, "wb") : nullptr;
    }();
    if (!output) return;
    static uint64_t ordinal = 0;
    std::fprintf(output, "{\"sequence\":%llu,\"kind\":\"%s\",\"pc\":%u,\"backend\":\"%s\",\"forced_tier3\":%s,\"cycles\":%llu,\"instruction\":%llu,\"r0\":%u,\"r1\":%u,\"lr\":%u}\n",
        (unsigned long long)++ordinal, kind, pc, backend, g_nds_force_tier3 ? "true" : "false",
        (unsigned long long)g_runtime_cycles, (unsigned long long)g_insn_count[0], registers[0], registers[1], registers[14]);
    std::fflush(output);
}

inline void compiled_instruction() {
    const uint32_t pc = g_cpu.R[15];
    const bool thumb = (g_cpu.cpsr & 0x20u) != 0u;
    observe_entry(pc, thumb, g_cpu.R, "compiled");
    if (g_nds_active == NDS_ARM9 && !thumb && pc == 0x0204d790u)
        before_instruction(pc, thumb, peek_word(pc), g_cpu.R, g_cpu.cpsr, "compiled");
}
}
