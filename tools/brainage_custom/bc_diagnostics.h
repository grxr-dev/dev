#pragma once

namespace brainage_custom::diagnostics {
inline FILE* trace = nullptr;
inline unsigned sequence = 0;
inline bool entry_observer = false;

inline void initialize() {
    const char* observer = std::getenv("NDS_TASK_K_TRACE");
    entry_observer = observer && *observer;
    const char* path = std::getenv("NDS_TASK_J_TRACE");
    if (path && *path) {
        trace = std::fopen(path, "wb");
        if (!trace) throw std::runtime_error("Brain Age audit trace cannot be opened");
    }
}

inline bool observing() {
    return trace || entry_observer;
}

inline void begin_session(Hold& hold) {
    if (!enabled || (!trace && !std::getenv("NDS_TASK_J_CONTROL"))) return;
    hold.audit.control.session = std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());
#if defined(_WIN32)
    hold.audit.control.session += "-" + std::to_string(GetCurrentProcessId());
#endif
}
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

inline std::vector<uint8_t> service_ram_before;
inline decltype(g_cpu) service_cpu_before{};
inline std::vector<uint8_t> mainram_snapshot() {
    std::vector<uint8_t> bytes(0x400000);for(unsigned i=0;i<bytes.size();++i)bytes[i]=bus_debug_read8(9,0x02000000+i);return bytes;
}
inline void service_isolation_begin() {if(trace){service_ram_before=mainram_snapshot();service_cpu_before=g_cpu;}}
inline void record_service_cleanup(const DigitResult& cleanup) {
    if(!trace)return;
    auto after=mainram_snapshot();
    if(after!=service_ram_before || std::memcmp(&service_cpu_before,&g_cpu,sizeof(g_cpu)))throw std::runtime_error("custom service changed live RAM/CPU");
    const auto* path=std::getenv("NDS_TASK_V_TRACE");
    FILE* service_trace=path?std::fopen(path,"a"):nullptr;
    if(service_trace)std::fprintf(service_trace,"{\"event\":\"service_cleanup\",\"active\":false,\"return\":%u,\"wall_us\":%llu,\"instructions\":%llu,\"ram_equal\":true,\"cpu_equal\":true,\"ram_sha256\":\"%s\"}\n",cleanup.error,(unsigned long long)cleanup.wall_us,(unsigned long long)cleanup.instructions,resource_detail::sha256(after.data(),after.size()).c_str());
    if(service_trace)std::fclose(service_trace);
    service_ram_before.clear();
}
inline void record(const char* event, const Hold& hold) {
    if (!trace) return;
    const auto status = exercise_status(hold);
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
        hold.backend, g_nds_force_tier3 ? "true" : "false", hold.audit.control.session.c_str(),
        status.phase.c_str(), unsigned(status.answers.size()), status.completed ? "true" : "false",
        status.can_continue ? "true" : "false", hold.audit.control.sequence, hold.audit.input_sequence,
        hold.audit.input_source, hold.audit.input_action, hold.audit.input_answer, hold.audit.rejection);
    for (unsigned index = 0; index < status.answers.size(); ++index)
        std::fprintf(trace, "%s%u", index ? "," : "", status.answers[index]);
    const auto touch = nds_touch_observation();
    std::fprintf(trace, "],\"touch_x\":%u,\"touch_y\":%u,\"touch_down\":%s,\"touch_target\":%u,\"touch_events\":%llu,\"consumed\":%s,\"touch_owner\":%s,\"native_contact\":%s,\"guest_pen_down\":%s,\"guest_adc_x\":%u,\"guest_adc_y\":%u,\"guest_touch_deliveries\":%llu,\"event_guest_deliveries\":%llu",
        hold.audit.touch_x, hold.audit.touch_y, hold.audit.touch_down ? "true" : "false", hold.audit.touch_target,
        (unsigned long long)hold.audit.touch_events, hold.audit.consumed ? "true" : "false", touch.owned ? "true" : "false",
        status.contact_down ? "true" : "false", touch.down ? "true" : "false", touch.adc_x, touch.adc_y,
        (unsigned long long)touch.guest_deliveries,
        (unsigned long long)(touch.guest_deliveries - hold.audit.delivery_before));
    if (ds_presentation) {
        uint16_t width = 256;
        const auto* bottom = nds_gpu2d_presented_framebuffer(1, &width, false);
        std::fprintf(trace, ",\"presentation_owner\":%s,\"bottom_source\":\"%s\",\"top_source\":\"guest\",\"surface_width\":%u,\"surface_height\":192,\"native_sha1\":\"%s\",\"presented_bottom_sha1\":\"%s\",\"guest_top_sha1\":\"%s\",\"guest_bottom_sha1\":\"%s\",\"video_sha1\":\"%s\",\"capture\":\"%s\",\"popup\":false",
            nds_gpu2d_bottom_presentation_owned() ? "true" : "false", nds_gpu2d_bottom_presentation_owned() ? "native" : "guest", width,
            hold.surface ? pixel_digest(hold.surface->pixels.data()).c_str() : "", pixel_digest(bottom).c_str(),
            pixel_digest(nds_gpu2d_framebuffer(0)).c_str(), pixel_digest(nds_gpu2d_framebuffer(1)).c_str(), video_digest().c_str(), hold.audit.capture_name);
    }
    std::fprintf(trace, ",\"exercise_id\":\"%s\",\"exercise_present\":%s,\"begin_count\":%u,\"render_count\":%u,\"exercise_touch_count\":%u,\"status_queries\":%u", hold.exercise_id, hold.exercise ? "true" : "false", hold.begin_count, hold.render_count, hold.touch_count, hold.status_queries);
    std::fprintf(trace, ",\"exercise_metrics\":{");
    for (unsigned index = 0; index < status.diagnostics.size(); ++index) {
        const auto& metric = status.diagnostics[index];
        if (metric.name.empty() || metric.name.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_") != std::string::npos)
            throw std::runtime_error("invalid exercise diagnostic metric name");
        std::fprintf(trace, "%s\"%s\":%llu", index ? "," : "", metric.name.c_str(), (unsigned long long)metric.value);
    }
    std::fprintf(trace, "},\"frontend_hold_presents\":%llu}\n", (unsigned long long)frontend_hold_presents());
    std::fflush(trace);
}

inline void capture_presented(Hold& hold, const char* name) {
    const char* root = std::getenv("NDS_TASK_N_CAPTURE_ROOT");
    if (!root || !*root) return;
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
    hold.audit.capture_name = name;
    record("capture_complete", hold);
    hold.audit.capture_name = "";
}


#if defined(_WIN32)
inline void paint_panel(HWND window, HDC dc) {
    auto* hold = reinterpret_cast<Hold*>(GetWindowLongPtrW(window, GWLP_USERDATA));
    if (!hold || !hold->surface) return;
    BITMAPINFO info{};
    info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    info.bmiHeader.biWidth = 256;
    info.bmiHeader.biHeight = -192;
    info.bmiHeader.biPlanes = 1;
    info.bmiHeader.biBitCount = 32;
    info.bmiHeader.biCompression = BI_RGB;
    StretchDIBits(dc, 0, 0, 512, 384, 0, 0, 256, 192, hold->surface->pixels.data(), &info, DIB_RGB_COLORS, SRCCOPY);
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


inline void apply_action(HWND, Hold& hold, const char* action, unsigned value) {
    hold.audit.input_action = action;
    hold.audit.input_answer = value;
    hold.audit.rejection = "";
    if (std::strcmp(action, "sample") == 0) record("held_sample", hold);
    else dispatch_action(hold, action, value);
}
inline void poll_control(HWND window, Hold* hold) {
    const char* path = std::getenv("NDS_TASK_J_CONTROL");
    FILE* input = path && *path ? std::fopen(path, "rb") : nullptr;
    if (input) {
        char line[256]{};
        const bool read = std::fgets(line, sizeof(line), input) != nullptr;
        std::fclose(input);
        if (read && hold->audit.last_input != line) {
            hold->audit.last_input = line;
            char token[96]{}, command[16]{}, trailing[2]{};
            unsigned number = 0, answer = 0;
            const int fields = std::sscanf(line, "%95s %u %15s %u %1s", token, &number, command, &answer, trailing);
            unsigned x = 0, y = 0, down = 0;
            const int touch_fields = std::sscanf(line, "%95s %u %15s %u %u %u %1s", token, &number, command, &x, &y, &down, trailing);
            char checkpoint[16]{}, extra[2]{};
            const int capture_fields = std::sscanf(line, "%95s %u %15s %15s %1s", token, &number, command, checkpoint, extra);
            const bool capture = ds_presentation && std::strcmp(command, "capture") == 0;
            const bool capture_format = capture_fields == 4 && *checkpoint && std::strspn(checkpoint, "abcdefghijklmnopqrstuvwxyz0123456789-") == std::strlen(checkpoint);
            const bool raw_touch = std::strcmp(command, "touch") == 0;
            hold->audit.input_source = "diagnostic";
            hold->audit.input_sequence = number;
            hold->audit.input_action = "invalid";
            hold->audit.input_answer = answer;
            const bool known_action = std::strcmp(command, "choose") == 0 || std::strcmp(command, "sample") == 0 || std::strcmp(command, "continue") == 0;
            const bool format_ok = capture ? capture_format : raw_touch ? touch_fields == 6 && x <= 255 && y <= 191 && down <= 1 :
                known_action && (std::strcmp(command, "choose") == 0 ? fields == 4 : fields == 3);
            const char* rejected = format_ok ? hold->audit.control.consume(token, number) : "invalid_format";
            if (rejected) {
                hold->audit.rejection = rejected;
                record("control_rejected", *hold);
            } else if (capture) {
                hold->audit.input_action = "capture";
                capture_presented(*hold, checkpoint);
            } else if (raw_touch) nds_set_touch(uint16_t(x), uint16_t(y), down != 0);
            else apply_action(window, *hold, command, answer);
        }
    }
}


inline LRESULT CALLBACK panel_proc(HWND window, UINT message, WPARAM parameter, LPARAM detail) {
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
    if (message == WM_LBUTTONDOWN || message == WM_LBUTTONUP) {
        nds_set_touch(uint16_t(LOWORD(detail) / 2), uint16_t(HIWORD(detail) / 2), message == WM_LBUTTONDOWN);
        return 0;
    }
    return DefWindowProcW(window, message, parameter, detail);
}
#endif

inline void refresh_panel(Hold& hold) {
#if defined(_WIN32)
    HWND window = static_cast<HWND>(hold.audit.window);
    if (window) {
        RedrawWindow(window, nullptr, nullptr, RDW_INVALIDATE | RDW_ERASE | RDW_UPDATENOW);
        capture_panel(window);
    }
#else
    (void)hold;
#endif
}

inline void create_panel(Hold& hold) {
#if defined(_WIN32)
    WNDCLASSW panel{};
    panel.lpfnWndProc = panel_proc;
    panel.hInstance = GetModuleHandleW(nullptr);
    panel.hCursor = LoadCursorW(nullptr, MAKEINTRESOURCEW(32512));
    panel.lpszClassName = L"BrainAgeTaskJNativeProbe";
    if (!RegisterClassW(&panel) && GetLastError() != ERROR_CLASS_ALREADY_EXISTS)
        throw std::runtime_error("Brain Age native panel class creation failed");
    RECT bounds{0, 0, 512, 384};
    const DWORD style = WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU;
    AdjustWindowRect(&bounds, style, FALSE);
    HWND window = CreateWindowExW(0, panel.lpszClassName, L"Brain Age Native Exercise Test", style,
        CW_USEDEFAULT, CW_USEDEFAULT, bounds.right - bounds.left, bounds.bottom - bounds.top,
        nullptr, nullptr, panel.hInstance, nullptr);
    if (!window) throw std::runtime_error("Brain Age native panel creation failed");
    hold.audit.window = window;
    SetWindowLongPtrW(window, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(&hold));
    ShowWindow(window, SW_SHOWNORMAL);
    UpdateWindow(window);
    capture_panel(window);
#else
    (void)hold;
    throw std::runtime_error("legacy native panel requires Windows");
#endif
}

inline void service_panel(Hold&) {
#if defined(_WIN32)
    MSG message{};
    while (PeekMessageW(&message, nullptr, 0, 0, PM_REMOVE)) {
        if (message.message == WM_QUIT) throw std::runtime_error("native panel cancelled");
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
#endif
}

inline void destroy_panel(Hold& hold) {
#if defined(_WIN32)
    if (hold.audit.window) DestroyWindow(static_cast<HWND>(hold.audit.window));
#endif
    hold.audit.window = nullptr;
}

inline void poll(Hold& hold) {
#if defined(_WIN32)
    poll_control(static_cast<HWND>(hold.audit.window), &hold);
#else
    (void)hold;
#endif
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

}
