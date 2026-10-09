#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

struct Target {
    DWORD pid;
    HWND window = nullptr;
    unsigned matches = 0;
};

BOOL CALLBACK find_window(HWND window, LPARAM parameter) {
    auto& target = *reinterpret_cast<Target*>(parameter);
    DWORD pid = 0;
    GetWindowThreadProcessId(window, &pid);
    if (pid == target.pid && IsWindowVisible(window) && !GetWindow(window, GW_OWNER)) {
        target.window = window;
        ++target.matches;
    }
    return TRUE;
}

std::string escaped(const char* text) {
    std::string result;
    for (; *text; ++text) {
        if (*text == '"' || *text == '\\') result += '\\';
        if (static_cast<unsigned char>(*text) >= 32) result += *text;
    }
    return result;
}

void check(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

void focus(HWND window) {
    ShowWindow(window, SW_RESTORE);
    SetWindowPos(window, HWND_TOP, 40, 40, 0, 0, SWP_NOSIZE | SWP_SHOWWINDOW);
    SetForegroundWindow(window);
    Sleep(250);
    if (GetForegroundWindow() != window) {
        HWND foreground = GetForegroundWindow();
        DWORD thread = foreground ? GetWindowThreadProcessId(foreground, nullptr) : 0;
        const DWORD current = GetCurrentThreadId();
        const bool attached = thread && thread != current && AttachThreadInput(current, thread, TRUE);
        SetForegroundWindow(window);
        if (attached) AttachThreadInput(current, thread, FALSE);
        Sleep(250);
    }
    check(GetForegroundWindow() == window, "foreground ownership could not be guaranteed");
}

void capture(HWND window, const RECT& client, const POINT& origin, const char* output, bool screen) {
    const int width = client.right, height = client.bottom;
    HDC source = GetDC(screen ? nullptr : window);
    check(source != nullptr, "capture DC unavailable");
    HDC memory = CreateCompatibleDC(source);
    BITMAPINFO info{};
    info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    info.bmiHeader.biWidth = width;
    info.bmiHeader.biHeight = -height;
    info.bmiHeader.biPlanes = 1;
    info.bmiHeader.biBitCount = 32;
    info.bmiHeader.biCompression = BI_RGB;
    void* pixels = nullptr;
    HBITMAP bitmap = CreateDIBSection(source, &info, DIB_RGB_COLORS, &pixels, nullptr, 0);
    check(bitmap && memory, "capture bitmap unavailable");
    HGDIOBJ previous = SelectObject(memory, bitmap);
    bool ok;
    if (screen) {
        for (int row = 1; row < height; row += 16)
            for (int column = 1; column < width; column += 16)
                check(GetAncestor(WindowFromPoint(POINT{origin.x + column, origin.y + row}), GA_ROOT) == window, "target client is obscured");
        ok = BitBlt(memory, 0, 0, width, height, source, origin.x, origin.y, SRCCOPY | CAPTUREBLT);
    } else {
        ok = PrintWindow(window, memory, PW_CLIENTONLY | 2);
    }
    check(ok, "window capture failed");
    BITMAPFILEHEADER header{};
    header.bfType = 0x4d42;
    header.bfOffBits = sizeof(header) + sizeof(info.bmiHeader);
    header.bfSize = header.bfOffBits + width * height * 4;
    std::ifstream existing(output, std::ios::binary);
    check(!existing.good(), "will not overwrite capture");
    std::ofstream file(output, std::ios::binary);
    file.write(reinterpret_cast<char*>(&header), sizeof(header));
    file.write(reinterpret_cast<char*>(&info.bmiHeader), sizeof(info.bmiHeader));
    file.write(static_cast<char*>(pixels), width * height * 4);
    check(file.good(), "capture file write failed");
    SelectObject(memory, previous);
    DeleteObject(bitmap);
    DeleteDC(memory);
    ReleaseDC(screen ? nullptr : window, source);
}

int main(int argc, char** argv) {
    try {
        check(argc >= 4, "usage: window_probe observe|place|capture|click PID expected-exe [arguments]");
        SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
        Target target{static_cast<DWORD>(std::stoul(argv[2]))};
        HANDLE process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, target.pid);
        check(process != nullptr, "runner process unavailable");
        char executable[32768]{};
        DWORD size = sizeof(executable);
        check(QueryFullProcessImageNameA(process, 0, executable, &size), "process identity unavailable");
        CloseHandle(process);
        check(_stricmp(executable, argv[3]) == 0, "process executable mismatch");
        EnumWindows(find_window, reinterpret_cast<LPARAM>(&target));
        check(target.matches == 1, "expected exactly one visible process-owned window");
        DWORD_PTR result = 0;
        check(SendMessageTimeoutW(target.window, WM_NULL, 0, 0, SMTO_ABORTIFHUNG, 2000, &result), "runner window unresponsive");
        const std::string action = argv[1];
        if (action == "expose") {
            ShowWindow(target.window, SW_SHOWNOACTIVATE);
            SetWindowPos(target.window, HWND_TOPMOST, 40, 40, 0, 0, SWP_NOSIZE | SWP_SHOWWINDOW | SWP_NOACTIVATE);
            Sleep(250);
        } else if (action != "observe" && action != "capture") focus(target.window);
        RECT client{}, window{};
        POINT origin{};
        check(GetClientRect(target.window, &client) && GetWindowRect(target.window, &window) && ClientToScreen(target.window, &origin), "window geometry unavailable");
        char title[512]{}, classname[256]{};
        GetWindowTextA(target.window, title, sizeof(title));
        GetClassNameA(target.window, classname, sizeof(classname));
        int client_x = -1, client_y = -1;
        POINT point{};
        if (action == "click") {
            check(argc == 6, "click requires CLIENT x y");
            client_x = std::stoi(argv[4]);
            client_y = std::stoi(argv[5]);
            check(client_x >= 0 && client_y >= 0 && client_x < client.right && client_y < client.bottom, "click outside client");
            point = {client_x, client_y};
            check(ClientToScreen(target.window, &point), "click transform failed");
            check(GetAncestor(WindowFromPoint(point), GA_ROOT) == target.window, "click target obscured");
            INPUT motion{};
            motion.type = INPUT_MOUSE;
            motion.mi.dx = MulDiv(point.x - GetSystemMetrics(SM_XVIRTUALSCREEN), 65535, GetSystemMetrics(SM_CXVIRTUALSCREEN) - 1);
            motion.mi.dy = MulDiv(point.y - GetSystemMetrics(SM_YVIRTUALSCREEN), 65535, GetSystemMetrics(SM_CYVIRTUALSCREEN) - 1);
            motion.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK;
            check(SendInput(1, &motion, sizeof(INPUT)) == 1, "mouse move rejected");
            Sleep(80);
            INPUT button{};
            button.type = INPUT_MOUSE;
            button.mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
            check(GetForegroundWindow() == target.window, "focus changed before click");
            check(SendInput(1, &button, sizeof(INPUT)) == 1, "mouse down rejected");
            Sleep(120);
            button.mi.dwFlags = MOUSEEVENTF_LEFTUP;
            check(SendInput(1, &button, sizeof(INPUT)) == 1, "mouse up rejected");
        } else if (action == "capture") {
            check(argc == 6, "capture requires output.bmp print|screen");
            check(std::string(argv[5]) == "print" || std::string(argv[5]) == "screen", "unknown capture method");
            capture(target.window, client, origin, argv[4], std::string(argv[5]) == "screen");
        } else check(action == "observe" || action == "place" || action == "expose", "unknown helper action");
        std::printf("{\"action\":\"%s\",\"pid\":%lu,\"hwnd\":%llu,\"title\":\"%s\",\"class\":\"%s\",\"dpi\":%u,\"client\":[%ld,%ld],\"origin\":[%ld,%ld],\"window\":[%ld,%ld,%ld,%ld],\"client_point\":[%d,%d],\"screen_point\":[%ld,%ld],\"foreground\":%s,\"foreground_hwnd\":%llu,\"source\":\"%s\"}\n",
            action.c_str(), target.pid, (unsigned long long)reinterpret_cast<uintptr_t>(target.window), escaped(title).c_str(), escaped(classname).c_str(), GetDpiForWindow(target.window), client.right, client.bottom, origin.x, origin.y, window.left, window.top, window.right, window.bottom, client_x, client_y, point.x, point.y, GetForegroundWindow() == target.window ? "true" : "false", (unsigned long long)reinterpret_cast<uintptr_t>(GetForegroundWindow()), action == "click" ? "win32_sendinput" : "win32_window_api");
        return 0;
    } catch (const std::exception& error) {
        std::fprintf(stderr, "%s\n", error.what());
        return 1;
    }
}
