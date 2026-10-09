    struct NativeServiceScope {
        ~NativeServiceScope() { g_native_hold_service = {}; }
    } native_service_scope;
    g_native_hold_service = [&]() {
        if (!nds_touch_observation().owned || !nds_gpu2d_bottom_presentation_owned()) return true;
        SDL_Event held_event{};
        while (SDL_PollEvent(&held_event)) {
            task_o_event_trace(held_event, true);
            convert_mouse_event_to_logical_coordinates(held_event, presentation);
            if (held_event.type == SDL_QUIT || sdl_window_event_is(held_event, SDL_EVENT_WINDOW_CLOSE_REQUESTED)) {
                running = false;
                return false;
            }
            if (sdl_window_event_is(held_event, SDL_EVENT_WINDOW_FOCUS_LOST) && mouse_down) {
                mouse_down = false;
                touch_release_pending = false;
                set_touch_from_mouse(0, 0, false, options.screen_layout, bottom_logical_width);
            }
            if ((held_event.type == SDL_MOUSEBUTTONDOWN || held_event.type == SDL_MOUSEBUTTONUP) &&
                held_event.button.button == SDL_BUTTON_LEFT && held_event.button.windowID == presentation.window_ids[1]) {
                mouse_down = held_event.type == SDL_MOUSEBUTTONDOWN;
                touch_release_pending = false;
                touch_frames_held = 0;
                set_touch_from_mouse(held_event.button.x, held_event.button.y, mouse_down, options.screen_layout, bottom_logical_width);
            }
            if (held_event.type == SDL_MOUSEMOTION && mouse_down && held_event.motion.windowID == presentation.window_ids[1])
                set_touch_from_mouse(held_event.motion.x, held_event.motion.y, true, options.screen_layout, bottom_logical_width);
        }
        const auto ticks = present_screens(presentation, nds_gpu2d_framebuffer(0), 256,
            nds_gpu2d_presented_framebuffer(1, nullptr, false), 256, runtime_ui, false, 0, 0, nullptr);
        if (ticks.ok) ++g_native_hold_presents;
        return ticks.ok;
    };
