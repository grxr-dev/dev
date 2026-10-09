"""Install bounded host-only servicing on the pinned Task N runtime."""

import argparse
import difflib
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-executable", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    subprocess.run(["python", str(root / "tools/task_k/install.py"), "--codex-executable", str(args.codex_executable)], check=True)
    pending = {}

    def update(name, marker, replacements):
        path = root / "local/ndsrecomp/runner/src" / name
        if name in pending:
            original, old = pending[name]
        else:
            original = old = path.read_text()
        if marker in old:
            return
        new = old
        for anchor, replacement in replacements:
            if new.count(anchor) != 1:
                raise ValueError(f"ambiguous pinned anchor in {name}: {anchor[:80]}")
            new = new.replace(anchor, replacement)
        pending[name] = (original, new)

    update("frontend.h", "nds_frontend_service_native_hold", [("#include <string>", "#include <string>\n\nbool nds_frontend_service_native_hold();\nuint64_t nds_frontend_native_present_count();")])
    update("frontend.h", "NDS_NATIVE_HOLD_FRONTEND_SERVICE", [("bool nds_frontend_service_native_hold();", "#define NDS_NATIVE_HOLD_FRONTEND_SERVICE 1\nbool nds_frontend_service_native_hold();")])
    update("frontend.cpp", "g_native_hold_service", [
        ("#include <fstream>", "#include <fstream>\n#include <functional>"),
        ("NdsFrontendLiveStats g_live_stats{};", "NdsFrontendLiveStats g_live_stats{};\nstd::function<bool()> g_native_hold_service;\nuint64_t g_native_hold_presents = 0;"),
        ("    while (running) {\n#if defined(NDS_HAVE_COMPUTE_RENDERER)", (root / "tools/task_o/hold_service.inc").read_text() + "\n    while (running) {\n#if defined(NDS_HAVE_COMPUTE_RENDERER)"),
        ("            convert_mouse_event_to_logical_coordinates(event, presentation);", "            task_o_event_trace(event, false);\n            convert_mouse_event_to_logical_coordinates(event, presentation);"),
        ("void set_touch_from_mouse(float x, float y, bool down,", (root / "tools/task_o/event_trace.inc").read_text() + "\nvoid set_touch_from_mouse(float x, float y, bool down,"),
        ("        nds_set_touch(0, 0, false);\n        return;", "        const auto before = nds_touch_observation();\n        nds_set_touch(0, 0, false);\n        task_o_touch_trace(x, y, 0, 0, down, before);\n        return;"),
        ("    nds_set_touch(touch_x, touch_y, true);", "    const auto before = nds_touch_observation();\n    nds_set_touch(touch_x, touch_y, true);\n    task_o_touch_trace(x, y, touch_x, touch_y, true, before);"),
        ("void nds_frontend_live_stats(NdsFrontendLiveStats* out)", "bool nds_frontend_service_native_hold() {\n    return !g_native_hold_service || g_native_hold_service();\n}\n\nuint64_t nds_frontend_native_present_count() { return g_native_hold_presents; }\n\nvoid nds_frontend_live_stats(NdsFrontendLiveStats* out)")
    ])
    update("debug_server.h", "debug_load_initial_state", [("void debug_serve(uint16_t port);", "bool debug_load_initial_state(const char* path, std::string* error);\nvoid debug_serve(uint16_t port);")])
    update("frontend.cpp", "task_o_queue_frontend_button", [
        ("#include <string>", "#include <string>\n#include <sstream>"),
        ("uint64_t task_o_input_sequence = 0;", (root / "tools/task_o/queue_input.inc").read_text() + "\nuint64_t task_o_input_sequence = 0;"),
        ("        SDL_Event held_event{};", "        task_o_queue_frontend_button(presentation.window_ids[1]);\n        SDL_Event held_event{};"),
        ("        SDL_Event event{};\n        while (SDL_PollEvent(&event))", "        task_o_queue_frontend_button(presentation.window_ids[1]);\n        SDL_Event event{};\n        while (SDL_PollEvent(&event))")
    ])
    update("debug_server.cpp", "debug_load_initial_state", [("void debug_set_savestate_identity(const std::string& build_id,", "bool debug_load_initial_state(const char* path, std::string* error) {\n    if (g_play_mode || g_savestate_identity.rom_sha1.empty()) {\n        *error = \"initial restoration requires pre-frontend ROM identity\";\n        return false;\n    }\n    return nds_savestate_load_core(path, g_savestate_identity, error);\n}\n\nvoid debug_set_savestate_identity(const std::string& build_id,")])
    update("main.cpp", "NDS_TASK_O_START_STATE", [("    boot();\n", "    boot();\n    if (const char* initial = std::getenv(\"NDS_TASK_O_START_STATE\")) {\n        std::string error;\n        if (!interactive || rom_sha1 != \"b8a105bacc3234dede8d4465df0869f2b922a0e2\" ||\n            !debug_load_initial_state(initial, &error)) {\n            std::fprintf(stderr, \"[task-o] initial restoration rejected: %s\\n\", error.c_str());\n            return 1;\n        }\n        g_nds_force_tier3 = false;\n        std::fprintf(stderr, \"[task-o] validated initial state restored; force-tier3 disabled before execution\\n\");\n    }\n")])
    changes = []
    for name, (old, new) in pending.items():
        difference = list(difflib.unified_diff(old.splitlines(), new.splitlines(), n=3))[2:]
        changes.append(f"*** Update File: local/ndsrecomp/runner/src/{name}\n" + "\n".join("@@" if line.startswith("@@") else line for line in difference))
    if changes:
        subprocess.run([str(args.codex_executable), "--codex-run-as-apply-patch", "*** Begin Patch\n" + "\n".join(changes) + "\n*** End Patch\n"], cwd=root, check=True)


if __name__ == "__main__":
    main()
