uint64_t task_o_input_sequence = 0;

void task_o_event_trace(const SDL_Event& event, bool held) {
    if (event.type != SDL_MOUSEBUTTONDOWN && event.type != SDL_MOUSEBUTTONUP) return;
    const char* path = std::getenv("NDS_TASK_O_FRONTEND_TRACE");
    if (!path || !*path) return;
    if (FILE* trace = std::fopen(path, "ab")) {
        std::fprintf(trace, "{\"event\":\"frontend_button\",\"sequence\":%llu,\"window_id\":%u,\"client_x\":%.3f,\"client_y\":%.3f,\"down\":%s,\"held\":%s}\n",
            (unsigned long long)++task_o_input_sequence, event.button.windowID,
            double(event.button.x), double(event.button.y), event.type == SDL_MOUSEBUTTONDOWN ? "true" : "false", held ? "true" : "false");
        std::fclose(trace);
    }
}

void task_o_touch_trace(float logical_x, float logical_y, unsigned x, unsigned y, bool down, const NdsTouchObservation& before) {
    const char* path = std::getenv("NDS_TASK_O_FRONTEND_TRACE");
    if (!path || !*path) return;
    const auto after = nds_touch_observation();
    if (FILE* trace = std::fopen(path, "ab")) {
        std::fprintf(trace, "{\"event\":\"frontend_touch\",\"sequence\":%llu,\"logical_x\":%.3f,\"logical_y\":%.3f,\"ds_x\":%u,\"ds_y\":%u,\"down\":%s,\"owner\":%s,\"guest_before\":%llu,\"guest_after\":%llu,\"consumed\":%s}\n",
            (unsigned long long)task_o_input_sequence, double(logical_x), double(logical_y), x, y, down ? "true" : "false", before.owned ? "true" : "false",
            (unsigned long long)before.guest_deliveries, (unsigned long long)after.guest_deliveries, before.owned ? "true" : "false");
        std::fclose(trace);
    }
}
