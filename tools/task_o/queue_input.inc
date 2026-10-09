void task_o_queue_frontend_button(uint32_t window_id) {
    const char* path = std::getenv("NDS_TASK_O_WINDOW_CONTROL");
    const char* token = std::getenv("NDS_TASK_O_CONTROL_TOKEN");
    if (!path || !token || !*token) return;
    static uint64_t accepted_sequence = 0;
    static bool queued_contact = false;
    static int previous_x = 0, previous_y = 0;
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
        (down < 0 || down > 2) || (down == 1 && queued_contact) || (down != 1 && !queued_contact) ||
        x < 0 || y < 0 || x >= width || y >= height) return;
    SDL_Event event{};
    if (down == 2) {
        event.type = SDL_MOUSEMOTION;
        event.motion.windowID = window_id;
        event.motion.state = SDL_BUTTON_LMASK;
        event.motion.x = x;
        event.motion.y = y;
        event.motion.xrel = x - previous_x;
        event.motion.yrel = y - previous_y;
    } else {
        event.type = down ? SDL_MOUSEBUTTONDOWN : SDL_MOUSEBUTTONUP;
        event.button.windowID = window_id;
        event.button.button = SDL_BUTTON_LEFT;
        sdl_set_mouse_button_state(event, down != 0);
        event.button.clicks = 1;
        event.button.x = x;
        event.button.y = y;
    }
    if (!sdl_push_event(event)) return;
    accepted_sequence = sequence;
    queued_contact = down != 0;
    previous_x = x;
    previous_y = y;
    if (const char* trace_path = std::getenv("NDS_TASK_O_FRONTEND_TRACE")) {
        if (FILE* trace = std::fopen(trace_path, "ab")) {
            std::fprintf(trace, "{\"event\":\"%s\",\"control_sequence\":%llu,\"client_x\":%d,\"client_y\":%d,\"down\":%s,\"window_id\":%u}\n",
                down == 2 ? "sdl_queue_motion" : "sdl_queue_button", (unsigned long long)sequence, x, y, down ? "true" : "false", window_id);
            std::fclose(trace);
        }
    }
}
