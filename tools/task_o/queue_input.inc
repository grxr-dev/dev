void task_o_queue_frontend_button(uint32_t window_id) {
    const char* path = std::getenv("NDS_TASK_O_WINDOW_CONTROL");
    const char* token = std::getenv("NDS_TASK_O_CONTROL_TOKEN");
    if (!path || !token || !*token) return;
    static uint64_t accepted_sequence = 0;
    static std::string previous;
    std::ifstream input(path);
    std::string line;
    if (!std::getline(input, line) || line == previous) return;
    previous = line;
    std::istringstream fields(line);
    std::string identity, extra;
    uint64_t sequence = 0;
    int down = -1, x = -1, y = -1;
    fields >> identity >> sequence >> down >> x >> y;
    SDL_Window* window = SDL_GetWindowFromID(window_id);
    int width = 0, height = 0;
    if (window) SDL_GetWindowSize(window, &width, &height);
    if (!fields || fields >> extra || identity != token || sequence != accepted_sequence + 1 ||
        (down != 0 && down != 1) || x < 0 || y < 0 || x >= width || y >= height) return;
    SDL_Event event{};
    event.type = down ? SDL_MOUSEBUTTONDOWN : SDL_MOUSEBUTTONUP;
    event.button.windowID = window_id;
    event.button.button = SDL_BUTTON_LEFT;
    sdl_set_mouse_button_state(event, down != 0);
    event.button.clicks = 1;
    event.button.x = x;
    event.button.y = y;
    if (!sdl_push_event(event)) return;
    accepted_sequence = sequence;
    if (const char* trace_path = std::getenv("NDS_TASK_O_FRONTEND_TRACE")) {
        if (FILE* trace = std::fopen(trace_path, "ab")) {
            std::fprintf(trace, "{\"event\":\"sdl_queue_button\",\"control_sequence\":%llu,\"client_x\":%d,\"client_y\":%d,\"down\":%s,\"window_id\":%u}\n",
                (unsigned long long)sequence, x, y, down ? "true" : "false", window_id);
            std::fclose(trace);
        }
    }
}
