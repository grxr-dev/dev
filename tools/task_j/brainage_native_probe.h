#pragma once

#include <array>
#include <cstdio>
#include <cstdlib>
#include <cstring>
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

namespace brainage_task_j {
inline bool identity_ok = false;
inline bool enabled = false;
inline bool used = false;
inline FILE* trace = nullptr;
inline unsigned sequence = 0;
inline void compiled_instruction();

inline void initialize(const char* rom_sha1) {
    identity_ok = rom_sha1 && std::strcmp(rom_sha1, "b8a105bacc3234dede8d4465df0869f2b922a0e2") == 0;
    const char* activation = std::getenv("NDS_TASK_J_CUSTOM_EXERCISE_PROBE");
    enabled = identity_ok && activation && std::strcmp(activation, "1") == 0;
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
    unsigned control_sequence = 0;
    const char* backend = "tier3";
};

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
    std::fprintf(trace, "],\"backend\":\"%s\",\"forced_tier3\":%s}\n", hold.backend, g_nds_force_tier3 ? "true" : "false");
    std::fflush(trace);
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
    RECT text{24, 24, bounds.right - 24, 160};
    DrawTextW(dc, L"Brain Age Native Hook Test\n\nCustom exercise slot reached\nGuest transition held until Continue", -1,
        &text, DT_LEFT | DT_WORDBREAK);
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
    FILE* output = std::fopen(path, "wb");
    if (!output) throw std::runtime_error("Task J panel capture cannot be opened");
    std::fwrite(&header, sizeof(header), 1, output);
    std::fwrite(&info.bmiHeader, sizeof(info.bmiHeader), 1, output);
    std::fwrite(pixels.data(), pixels.size(), 1, output);
    std::fclose(output);
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
    if (hold && message == WM_COMMAND && LOWORD(parameter) == 1 && HIWORD(parameter) == BN_CLICKED) {
        hold->continued = true;
        return 0;
    }
    if (hold && message == WM_TIMER) {
        const char* path = std::getenv("NDS_TASK_J_CONTROL");
        FILE* input = path && *path ? std::fopen(path, "rb") : nullptr;
        if (input) {
            char command[16]{};
            unsigned number = 0;
            const bool parsed = std::fscanf(input, "%15s %u", command, &number) == 2;
            std::fclose(input);
            if (parsed && number > hold->control_sequence) {
                hold->control_sequence = number;
                if (std::strcmp(command, "sample") == 0) record("held_sample", *hold);
                if (std::strcmp(command, "continue") == 0) hold->continued = true;
            }
        }
        return 0;
    }
    return DefWindowProcW(window, message, parameter, detail);
}

inline void show_panel(Hold& hold) {
    WNDCLASSW panel{};
    panel.lpfnWndProc = panel_proc;
    panel.hInstance = GetModuleHandleW(nullptr);
    panel.hCursor = LoadCursorW(nullptr, MAKEINTRESOURCEW(32512));
    panel.lpszClassName = L"BrainAgeTaskJNativeProbe";
    if (!RegisterClassW(&panel) && GetLastError() != ERROR_CLASS_ALREADY_EXISTS)
        throw std::runtime_error("Task J panel class creation failed");
    HWND window = CreateWindowExW(0, panel.lpszClassName, L"Brain Age Native Hook Test",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU, CW_USEDEFAULT, CW_USEDEFAULT, 500, 280,
        nullptr, nullptr, panel.hInstance, nullptr);
    if (!window) throw std::runtime_error("Task J native window creation failed");
    SetWindowLongPtrW(window, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(&hold));
    HWND button = CreateWindowExW(0, L"BUTTON", L"Continue to Calculations x20",
        WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON, 110, 178, 280, 42,
        window, reinterpret_cast<HMENU>(1), panel.hInstance, nullptr);
    if (!button) throw std::runtime_error("Task J Continue control creation failed");
    SendMessageW(button, WM_SETFONT, reinterpret_cast<WPARAM>(GetStockObject(DEFAULT_GUI_FONT)), TRUE);
    ShowWindow(window, SW_SHOWNORMAL);
    UpdateWindow(window);
    capture_panel(window);
    if (!SetTimer(window, 1, 50, nullptr)) throw std::runtime_error("Task J input polling failed");
    record("panel_active", hold);
    MSG message{};
    while (!hold.continued) {
        if (GetMessageW(&message, nullptr, 0, 0) <= 0)
            throw std::runtime_error("Task J panel interrupted without Continue");
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
    KillTimer(window, 1);
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
    record(enabled ? "intercept" : "boundary_disabled", hold);
    if (!enabled) return;
#if defined(_WIN32)
    show_panel(hold);
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
